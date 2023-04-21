# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""This module contains the behaviours for the 'keep3r_job_abci' skill."""
import json
from abc import ABC
from typing import Any, Dict, Generator, Optional, Set, Tuple, Type, cast

from aea.configurations.data_types import PublicId


try:
    from typing import TypedDict  # >=py3.8
except ImportError:
    from mypy_extensions import TypedDict  # <=py3.7

from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.keep3r_v1.contract import Keep3rV1Contract
from packages.valory.contracts.keep3r_v2.contract import KeeperV2
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)
from packages.valory.skills.keep3r_job_abci.dynamic_package_loader import load_contract
from packages.valory.skills.keep3r_job_abci.io_.loader import ContractPackageLoader
from packages.valory.skills.keep3r_job_abci.models import Params, SharedState
from packages.valory.skills.keep3r_job_abci.payloads import (
    ActivationTxPayload,
    ApproveBondTxPayload,
    BondingTxPayload,
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    PathSelectionPayload,
    TopUpPayload,
    WaitingPayload,
    WorkTxPayload,
)
from packages.valory.skills.keep3r_job_abci.rounds import (
    ActivationRound,
    ApproveBondRound,
    AwaitTopUpRound,
    BondingRound,
    GetJobsRound,
    IsProfitableRound,
    IsWorkableRound,
    Keep3rJobAbciApp,
    PathSelectionRound,
    PerformWorkRound,
    SynchronizedData,
    WaitingRound,
)
from packages.valory.skills.transaction_settlement_abci.payload_tools import (
    hash_payload_to_hex,
)


SafeTx = TypedDict(
    "SafeTx",
    {
        "data": bytes,
        "gas": int,
        "to": str,
        "value": int,
        "gas_limit": int,
    },
)

# setting the safe gas to 0 means that all available gas will be used
# which is what we want in most cases
# more info here: https://safe-docs.dev.gnosisdev.com/safe/docs/contracts_tx_execution/
SAFE_GAS = 0

ZERO_ETH = 0

AUTO_GAS_LIMIT = 0


class Keep3rJobBaseBehaviour(BaseBehaviour, ABC):
    """Base state behaviour for the simple abci skill."""

    def __init__(self, **kwargs: Any) -> None:
        """Init behaviour"""
        super().__init__(**kwargs, loader_cls=ContractPackageLoader)

    job_to_contract_id: Dict[str, PublicId] = {}

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Return the synchronized data."""
        return cast(SynchronizedData, super().synchronized_data)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

    @property
    def keep3r_v1_contract_address(self) -> str:
        """Return Keep3r V1 Contract address."""
        return self.context.params.keep3r_v1_contract_address

    @property
    def keep3r_v2_contract_address(self) -> str:
        """Return Keep3r V2 Contract address."""
        return self.context.params.keep3r_v2_contract_address

    @property
    def use_flashbots(self) -> bool:
        """Return if we are using flashbots."""
        return self.context.params.use_flashbots

    @property
    def bond_spender(self) -> str:
        """Return the bond spender."""
        if self.context.params.use_v2:
            return self.keep3r_v2_contract_address
        return self.keep3r_v1_contract_address

    @property
    def manual_gas_limit(self) -> int:
        """Return the manual gas limit."""
        return self.context.params.manual_gas_limit

    def _call_keep3r_v1(
        self, **kwargs: Any
    ) -> Generator[None, None, ContractApiMessage]:
        """Helper method"""
        kwargs = {
            "contract_address": self.keep3r_v1_contract_address,
            "contract_id": str(Keep3rV1Contract.contract_id),
            **kwargs,
        }
        contract_api_response = yield from self.get_contract_api_response(**kwargs)
        self.context.logger.info(f"Keep3r v1 response: {contract_api_response}")
        return contract_api_response

    def _call_keep3r_v2(
        self, **kwargs: Any
    ) -> Generator[None, None, ContractApiMessage]:
        """Helper method"""
        kwargs = {
            "contract_address": self.keep3r_v2_contract_address,
            "contract_id": str(KeeperV2.contract_id),
            **kwargs,
        }
        contract_api_response = yield from self.get_contract_api_response(**kwargs)
        self.context.logger.info(f"Keep3r v2 response: {contract_api_response}")
        return contract_api_response

    def read_keep3r(self, method: str, **kwargs: Any) -> Generator[None, None, Any]:
        """Read Keep3r contract state"""

        kwargs["performative"] = ContractApiMessage.Performative.GET_STATE
        kwargs["contract_callable"] = method
        if self.context.params.use_v2:
            contract_api_response = yield from self._call_keep3r_v2(**kwargs)
        else:
            contract_api_response = yield from self._call_keep3r_v1(**kwargs)
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(f"Failed read_keep3r: {contract_api_response}")
            return None
        return contract_api_response.state.body.get("data")

    def has_bonded(
        self, address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[bool]]:
        """Check start of bonding time of the address"""
        if self.context.params.use_v2:
            can_activate_after = yield from self.read_keep3r(
                "can_activate_after",
                address=address,
                bonding_asset=bonding_asset,
            )
            if can_activate_after is None:
                # something went wrong
                return None
            return can_activate_after != 0

        bond_time = yield from self.read_keep3r(
            "bondings",
            address=address,
            bonding_asset=bonding_asset,
        )
        if bond_time is None:
            log_msg = "Failed to check `bondings` on Keep3rV1 contract"
            self.context.logger.error(log_msg)
            return None
        return bond_time != 0

    def build_activate_tx(
        self, address: str
    ) -> Generator[None, None, Optional[SafeTx]]:
        """Build Keep3r V1 raw transaction"""
        data_str = yield from self.read_keep3r(
            method="build_activate_tx", address=address
        )
        if data_str is None:
            # something went wrong
            return None
        data = bytes.fromhex(data_str[2:])
        safe_tx = SafeTx(
            data=data,
            to=self.bond_spender,
            value=ZERO_ETH,
            gas=SAFE_GAS,
            gas_limit=AUTO_GAS_LIMIT,
        )
        return safe_tx

    def is_ready_to_activate(
        self, keeper: str, bonding_asset: str
    ) -> Generator[None, None, Optional[bool]]:
        """Check if the bond is ready to be activated"""
        if self.context.params.use_v2:
            can_activate_after = yield from self.read_keep3r(
                "can_activate_after",
                address=keeper,
                bonding_asset=bonding_asset,
            )
            if can_activate_after is None:
                # something went wrong
                return None
        else:
            bond_time = yield from self.read_keep3r(
                "bondings",
                address=keeper,
                bonding_asset=bonding_asset,
            )
            if bond_time is None:
                # something went wrong
                return None

            bond = yield from self.read_keep3r("bond")  # contract parameter
            if bond is None:
                return None
            can_activate_after = bond_time + bond

        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_block",
            block_identifier="latest",
        )
        if ledger_api_response.performative != LedgerApiMessage.Performative.STATE:
            log_msg = "Failed ledger get_block call in has_bonded"
            self.context.logger.error(f"{log_msg}: {ledger_api_response}")
            return None
        latest_block_timestamp = cast(
            int, ledger_api_response.state.body.get("timestamp")
        )
        remaining_time = can_activate_after - latest_block_timestamp
        self.context.logger.info(f"Remaining bond time: {remaining_time}")
        return remaining_time <= 0

    def has_activated(self, address: str) -> Generator[None, None, Optional[bool]]:
        """Check if bonding is completed"""
        is_keeper = yield from self.read_keep3r("is_keeper", address=address)
        return is_keeper

    def has_sufficient_funds(self, address: str) -> Generator[None, None, bool]:
        """Has sufficient funds"""

        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_balance",
            account=address,
        )
        if ledger_api_response.performative != LedgerApiMessage.Performative.STATE:
            return False  # transition to await top-up round
        balance = cast(int, ledger_api_response.state.body.get("get_balance_result"))
        self.context.logger.info(f"balance: {balance / 10 ** 18} ETH")
        return balance >= cast(int, self.context.params.insufficient_funds_threshold)

    def amount_to_approve(
        self, owner: str, spender: str, bonding_asset: str, bond_amount: int
    ) -> Generator[None, None, Optional[int]]:
        """Amount to approve"""
        kwargs = {
            "performative": ContractApiMessage.Performative.GET_STATE,
            "contract_callable": "allowance",
            "contract_address": bonding_asset,
            "owner": owner,
            "spender": spender,
        }
        allowance_msg = yield from self._call_keep3r_v1(**kwargs)
        if allowance_msg.performative != ContractApiMessage.Performative.STATE:
            # something went wrong
            log_msg = "Failed ledger allowance call"
            self.context.logger.error(f"{log_msg}: {allowance_msg}")
            return None
        allowance = cast(int, allowance_msg.state.body.get("data"))
        return bond_amount - allowance

    def has_pending_bond(
        self, address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[bool]]:
        """Check if bonding is completed"""
        if not self.context.params.use_v2:
            # only v2 has support for pending bonds
            return False
        pending_bond = yield from self.read_keep3r(
            "pending_bonds",
            address=address,
            bonding_asset=bonding_asset,
        )
        if pending_bond is None:
            # something went wrong
            return None
        return pending_bond > 0

    def get_off_chain_data(
        self,
        contract_address: str,
        contract_id: PublicId,
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Get off-chain data"""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=contract_address,
            contract_id=str(contract_id),
            contract_callable="get_off_chain_data",
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Failed get_off_chain_data: {contract_api_response}"
            )
            return None
        log_msg = (
            f"`get_off_chain_data` contract api response on {contract_api_response}"
        )
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(Dict[str, Any], contract_api_response.state.body)

    def simulate_tx(
        self,
        contract_address: str,
        contract_id: PublicId,
        data: bytes,
        safe_address: str,
    ) -> Generator[None, None, Optional[bool]]:
        """Get off-chain data"""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=contract_address,
            contract_id=str(contract_id),
            contract_callable="simulate_tx",
            keep3r_address=safe_address,
            data=data,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(f"Failed simulate_tx: {contract_api_response}")
            return None
        log_msg = f"`simulate_tx` contract api response on {contract_api_response}"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(bool, contract_api_response.state.body.get("data", False))

    def is_workable_job(
        self,
        contract_address: str,
        contract_id: PublicId,
        safe_address: str,
        **kwargs: Any,
    ) -> Generator[None, None, Optional[bool]]:
        """Check if job contract is workable"""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=contract_address,
            keep3r_address=safe_address,
            contract_id=str(contract_id),
            contract_callable="workable",
            **kwargs,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Failed is_workable_job: {contract_api_response}"
            )
            return False
        log_msg = f"`workable` contract api response on {contract_api_response}"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(bool, contract_api_response.state.body.get("data"))

    def build_approve_raw_tx(
        self, spender: str, bonding_asset: str, bond_amount: int
    ) -> Generator[None, None, Optional[SafeTx]]:
        """Build ERC20 approve transaction"""
        contract_api_response = yield from self._call_keep3r_v1(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_callable="build_approve_tx",
            contract_address=bonding_asset,
            spender=spender,
            amount=bond_amount,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            # something went wrong
            log_msg = (
                f"`build_approve_tx` contract api response on {contract_api_response}"
            )
            self.context.logger.info(f"{log_msg}: {contract_api_response}")
            return None
        data_str = cast(str, contract_api_response.state.body.get("data"))
        if data_str is None:
            # something went wrong
            return None
        data = bytes.fromhex(data_str[2:])
        safe_tx = SafeTx(
            data=data,
            to=bonding_asset,
            value=ZERO_ETH,
            gas=SAFE_GAS,
            gas_limit=AUTO_GAS_LIMIT,
        )
        return safe_tx

    def build_work_raw_tx(
        self,
        job_address: str,
        contract_id: PublicId,
        safe_address: str,
        **kwargs: Any,
    ) -> Generator[None, None, Optional[SafeTx]]:
        """Build raw work transaction for a job contract"""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_id=str(contract_id),
            contract_callable="build_work_tx",
            contract_address=job_address,
            keep3r_address=safe_address,
            **kwargs,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Failed build_work_raw_tx: {contract_api_response}"
            )
            return None
        log_msg = f"`build_work_tx` contract api response on {contract_api_response}"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")

        data_str = cast(str, contract_api_response.state.body["data"])[2:]
        data = bytes.fromhex(data_str)
        safe_tx = SafeTx(
            data=data,
            to=job_address,
            value=ZERO_ETH,
            gas=SAFE_GAS,
            gas_limit=self.manual_gas_limit,
        )
        return safe_tx

    def build_safe_raw_tx(
        self,
        tx_params: SafeTx,
    ) -> Generator[None, None, Optional[str]]:
        """Build safe raw tx hash"""

        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=tx_params["to"],
            value=tx_params["value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["gas"],
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.warning("build_safe_raw_tx unsuccessful!")
            return None

        # strip "0x" from the response hash
        tx_hash = cast(str, contract_api_response.state.body["tx_hash"])[2:]
        payload_data = hash_payload_to_hex(
            safe_tx_hash=tx_hash,
            ether_value=ZERO_ETH,  # we don't send any eth
            safe_tx_gas=SAFE_GAS,
            to_address=tx_params["to"],
            data=tx_params["data"],
            use_flashbots=self.use_flashbots,
            gas_limit=tx_params["gas_limit"],
        )
        return payload_data

    def _load_contract_package(
        self, ipfs_hash: str
    ) -> Generator[None, None, Optional[PublicId]]:
        """Fetch & load a contract package from IPFS."""
        self.context.logger.info(f"Loading contract package for {ipfs_hash}")
        job_package = yield from self.get_from_ipfs(ipfs_hash)
        if job_package is None:
            self.context.logger.error("Failed to get the package from IPFS!")
            return None
        contract_yaml, contract_py, abi_json = cast(Tuple[Dict, str, Dict], job_package)
        contract_id = load_contract(contract_py, contract_yaml, abi_json)
        if contract_id is None:
            self.context.logger.error("Failed to load the contract package!")
            return None
        return contract_id

    def _load_contract_packages(
        self, address_to_hash: Dict[str, str]
    ) -> Generator[None, None, Dict[str, PublicId]]:
        """Load contract packages from IPFS"""
        address_to_public_id: Dict[str, PublicId] = {}
        for address, ipfs_hash in address_to_hash.items():
            contract_id = yield from self._load_contract_package(ipfs_hash)
            if contract_id is None:
                self.context.logger.error(
                    f"Failed to load contract package with ipfs hash {ipfs_hash}!"
                )
                continue
            self.context.logger.info(f"Loaded contract package {contract_id}")
            address_to_public_id[address] = contract_id
        return address_to_public_id

    def dynamically_load_contracts(
        self, address_to_hash: Dict[str, str]
    ) -> Generator[None, None, None]:
        """Dynamically load contract packages from IPFS"""
        address_to_public_id = yield from self._load_contract_packages(address_to_hash)
        shared_state = cast(SharedState, self.context.state)
        # extend the shared state with the just loaded contracts
        shared_state.job_address_to_public_id = {
            **shared_state.job_address_to_public_id,
            **address_to_public_id,
        }


class PathSelectionBehaviour(Keep3rJobBaseBehaviour):
    """PathSelectionBehaviour"""

    matching_round: Type[AbstractRound] = PathSelectionRound
    transitions = PathSelectionRound.transitions

    def select_path(  # pylint: disable=R0911
        self,
    ) -> Generator[None, None, Optional[str]]:
        """Select path to traverse"""

        # check if job contract packages are loaded
        shared_state = cast(SharedState, self.context.state)
        loaded_contracts = shared_state.job_address_to_public_id
        supported_contracts = self.params.supported_jobs_to_package_hash
        if len(loaded_contracts) < len(supported_contracts):
            # if not, load them
            all_supported_jobs = self.params.supported_jobs_to_package_hash
            yield from self.dynamically_load_contracts(all_supported_jobs)

        safe_address = self.synchronized_data.safe_contract_address
        if not self.context.params.use_v2:
            # only keep3r v1 has "blacklist" functionality
            blacklisted = yield from self.read_keep3r("blacklist", address=safe_address)
            if blacklisted is None:
                return None
            if blacklisted:
                return self.transitions["BLACKLISTED"].name

        sufficient_funds = yield from self.has_sufficient_funds(safe_address)
        if sufficient_funds is None:
            return None
        if not sufficient_funds:
            return self.transitions["INSUFFICIENT_FUNDS"].name

        has_bonded = yield from self.has_bonded(
            safe_address, self.context.params.bonding_asset
        )
        if has_bonded is None:
            # something went wrong
            return None
        if not has_bonded:
            amount_to_approve = yield from self.amount_to_approve(
                owner=safe_address,
                spender=self.bond_spender,
                bonding_asset=self.context.params.bonding_asset,
                bond_amount=self.context.params.bond_amount,
            )
            if amount_to_approve is None:
                # something went wrong
                return None
            has_pending_bond = yield from self.has_pending_bond(
                safe_address, self.context.params.bonding_asset
            )
            if has_pending_bond is None:
                # something went wrong
                return None
            if amount_to_approve > 0 and not has_pending_bond:
                return self.transitions["APPROVE_BOND"].name
            return self.transitions["NOT_BONDED"].name

        bonded_keeper = yield from self.is_ready_to_activate(
            safe_address, self.context.params.bonding_asset
        )
        has_activated = yield from self.has_activated(safe_address)
        if has_activated is None or bonded_keeper is None:
            return None
        if has_activated:
            # we check first if we are activated, because we can be bonded and activated at the same time
            # this can happen if we decide to increase the bond.
            return self.transitions["HEALTHY"].name

        return self.transitions["NOT_ACTIVATED"].name

    def async_act(self) -> Generator:
        """Behaviour to select the path to traverse"""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            path = yield from self.select_path()
            if path is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            payload = PathSelectionPayload(self.context.agent_address, path)
            self.context.logger.info(f"Selected path: {path}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ApproveBondBehaviour(Keep3rJobBaseBehaviour):
    """Behaviour to prepare an ERC20 approve transaction."""

    matching_round: Type[AbstractRound] = ApproveBondRound

    def async_act(self) -> Generator:
        """Behaviour to prepare an ERC20 approve transaction."""
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            raw_tx = yield from self.build_approve_raw_tx(
                spender=self.bond_spender,
                bonding_asset=self.context.params.bonding_asset,
                bond_amount=self.context.params.bond_amount,
            )
            if raw_tx is None:
                # something went wrong
                yield from self.sleep(self.context.params.sleep_time)
                return

            self.context.logger.info(f"Prepared raw approve tx: {raw_tx}")

            safe_tx = yield from self.build_safe_raw_tx(raw_tx)
            if safe_tx is None:
                # something went wrong
                yield from self.sleep(self.context.params.sleep_time)
                return

            self.context.logger.info(f"Prepared safe tx: {safe_tx}")
            payload = ApproveBondTxPayload(
                self.context.agent_address,
                safe_tx,
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class BondingBehaviour(Keep3rJobBaseBehaviour):
    """BondingBehaviour"""

    matching_round: Type[AbstractRound] = BondingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            raw_tx = yield from self._build_bond_tx()
            if raw_tx is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            self.context.logger.info(f"Bonding raw tx: {raw_tx}")
            bonding_tx = yield from self.build_safe_raw_tx(cast(SafeTx, raw_tx))
            if not bonding_tx:
                yield from self.sleep(self.context.params.sleep_time)
                return
            payload = BondingTxPayload(
                self.context.agent_address, bonding_tx=bonding_tx
            )
            self.context.logger.info(f"Bonding tx: {bonding_tx}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _build_bond_tx(self) -> Generator[None, None, Optional[SafeTx]]:
        """Build bond tx"""
        data_str = yield from self.read_keep3r(
            method="build_bond_tx",
            address=self.context.params.bonding_asset,
            amount=self.context.params.bond_amount,
        )
        if data_str is None:
            # something went wrong
            return None
        data = bytes.fromhex(data_str[2:])
        safe_tx = SafeTx(
            data=data,
            to=self.bond_spender,
            value=ZERO_ETH,
            gas=SAFE_GAS,
            gas_limit=AUTO_GAS_LIMIT,
        )
        return safe_tx


class WaitingBehaviour(Keep3rJobBaseBehaviour):
    """WaitingBehaviour"""

    matching_round: Type[AbstractRound] = WaitingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            address = self.synchronized_data.safe_contract_address
            done_waiting = yield from self.is_ready_to_activate(
                keeper=address, bonding_asset=self.context.params.bonding_asset
            )
            if not done_waiting:  # when `None` or `False`
                yield from self.sleep(self.context.params.sleep_time)
                return
            payload = WaitingPayload(
                self.context.agent_address, done_waiting=done_waiting
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class ActivationBehaviour(Keep3rJobBaseBehaviour):
    """ActivationBehaviour"""

    matching_round: Type[AbstractRound] = ActivationRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            raw_tx = yield from self.build_activate_tx(
                self.context.params.bonding_asset
            )
            if raw_tx is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            self.context.logger.info(f"Activation raw tx: {raw_tx}")
            activation_tx = yield from self.build_safe_raw_tx(raw_tx)
            if activation_tx is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            self.context.logger.info(f"Activation tx: {activation_tx}")
            payload = ActivationTxPayload(
                self.context.agent_address, activation_tx=activation_tx
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class GetJobsBehaviour(Keep3rJobBaseBehaviour):
    """GetJobsBehaviour"""

    matching_round: Type[AbstractRound] = GetJobsRound

    def async_act(self) -> Generator:
        """Behaviour to get the current job listing"""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            job_list = yield from self.read_keep3r("get_jobs")
            if job_list is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            shared_state = cast(SharedState, self.context.state)
            supported_jobs_set = set(job_list).intersection(
                set(shared_state.job_address_to_public_id.keys())
            )
            supported_jobs = sorted(list(supported_jobs_set))
            job_list_str = json.dumps(supported_jobs)
            payload = GetJobsPayload(self.context.agent_address, job_list=job_list_str)
            self.context.logger.info(f"Job list retrieved: {job_list}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class IsWorkableBehaviour(Keep3rJobBaseBehaviour):
    """IsWorkableBehaviour"""

    matching_round: Type[AbstractRound] = IsWorkableRound

    def async_act(self) -> Generator:
        """Behaviour to get whether job is workable."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            workable_job = yield from self._get_workable_job()
            if workable_job is None:
                # no workable job
                workable_job = IsWorkableRound.NO_WORKABLE_JOB_PAYLOAD
            payload = IsWorkablePayload(self.context.agent_address, workable_job)
        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _is_workable(self, job_address: str) -> Generator[None, None, bool]:
        """Check if job is workable."""
        if job_address not in self.context.state.job_address_to_public_id:
            # if this contract is not loaded yet, load it this can happen if this agent is restarted
            job_hash = self.params.supported_jobs_to_package_hash[job_address]
            yield from self.dynamically_load_contracts({job_address: job_hash})
        contract_public_id = self.context.state.job_address_to_public_id[job_address]
        off_chain_data = yield from self.get_off_chain_data(
            job_address,
            contract_public_id,
        )
        if off_chain_data is None:
            # something went wrong, assume this job is not workable
            return False
        is_workable = yield from self.is_workable_job(
            job_address,
            contract_public_id,
            self.synchronized_data.safe_contract_address,
            **off_chain_data,
        )
        if is_workable is None:
            # something went wrong, assume this job is not workable
            return False

        return is_workable

    def _get_workable_job(self) -> Optional[str]:
        """Get the workable jobs."""
        job_list = self.synchronized_data.job_list
        job_list.sort()
        for job in job_list:
            is_workable = yield from self._is_workable(job)
            if is_workable:
                return job
        return None


class IsProfitableBehaviour(Keep3rJobBaseBehaviour):
    """IsProfitableBehaviour"""

    matching_round: Type[AbstractRound] = IsProfitableRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            job_address = self.synchronized_data.workable_job
            reward = yield from self.read_keep3r("credits", address=job_address)
            if reward is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            is_profitable = reward >= self.context.params.profitability_threshold
            self.context.logger.info(f"reward: {reward}, profitable: {is_profitable}")
            payload = IsProfitablePayload(self.context.agent_address, is_profitable)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PerformWorkBehaviour(Keep3rJobBaseBehaviour):
    """PerformWorkBehaviour"""

    matching_round: Type[AbstractRound] = PerformWorkRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            job_address = cast(str, self.synchronized_data.workable_job)
            if job_address not in self.context.state.job_address_to_public_id:
                # if this contract is not loaded yet, load it this can happen if this agent is restarted
                job_hash = self.params.supported_jobs_to_package_hash[job_address]
                yield from self.dynamically_load_contracts({job_address: job_hash})

            contract_public_id = self.context.state.job_address_to_public_id[
                job_address
            ]
            off_chain_data = yield from self.get_off_chain_data(
                job_address,
                contract_public_id,
            )
            if off_chain_data is None:
                # something went wrong
                yield from self.sleep(self.context.params.sleep_time)
                return
            safe_address = self.synchronized_data.safe_contract_address
            raw_tx = yield from self.build_work_raw_tx(
                job_address,
                contract_public_id,
                safe_address,
                **off_chain_data,
            )
            if raw_tx is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            tx_data = raw_tx.get("data")
            simulation_ok = yield from self.simulate_tx(
                job_address,
                contract_public_id,
                tx_data,
                safe_address,
            )
            if simulation_ok is None:
                # something went wrong while simulating
                yield from self.sleep(self.context.params.sleep_time)
                return
            if not simulation_ok:
                # simulation failed, i.e. a bad tx
                self.context.logger.info(
                    f"Simulating a work tx for job {job_address} failed. "
                    f"Tx data: {tx_data.hex()}."
                )
                work_tx = cast(
                    PerformWorkRound, self.matching_round
                ).SIMULATION_FAILED_PAYLOAD
            else:
                work_tx = yield from self.build_safe_raw_tx(raw_tx)
                if work_tx is None:
                    yield from self.sleep(self.context.params.sleep_time)
                    return
            payload = WorkTxPayload(self.context.agent_address, work_tx)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class AwaitTopUpBehaviour(Keep3rJobBaseBehaviour):
    """AwaitTopUpBehaviour"""

    matching_round: Type[AbstractRound] = AwaitTopUpRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            address = self.synchronized_data.safe_contract_address
            is_sufficient = yield from self.has_sufficient_funds(address)
            payload = TopUpPayload(self.context.agent_address, is_sufficient)
            self.context.logger.info(f"await_top_up sufficient: {is_sufficient}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class Keep3rJobRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the Keep3rJobAbciApp."""

    initial_behaviour_cls = BondingBehaviour
    abci_app_cls = Keep3rJobAbciApp  # type: ignore
    behaviours: Set[Type[BaseBehaviour]] = {
        ApproveBondBehaviour,  # type: ignore
        PathSelectionBehaviour,  # type: ignore
        BondingBehaviour,  # type: ignore
        WaitingBehaviour,  # type: ignore
        ActivationBehaviour,  # type: ignore
        GetJobsBehaviour,  # type: ignore
        IsWorkableBehaviour,  # type: ignore
        IsProfitableBehaviour,  # type: ignore
        PerformWorkBehaviour,  # type: ignore
        AwaitTopUpBehaviour,  # type: ignore
    }
