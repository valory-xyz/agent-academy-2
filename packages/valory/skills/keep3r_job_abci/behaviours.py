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
from typing import Any, Dict, Generator, List, Optional, Set, Tuple, Type, cast

from aea.configurations.data_types import PublicId
from hexbytes import HexBytes

from packages.valory.contracts.curve_pool.contract import CurvePoolContract
from packages.valory.contracts.multisend.contract import (
    MultiSendContract,
    MultiSendOperation,
)


try:
    from typing import TypedDict  # >=py3.8
except ImportError:
    from mypy_extensions import TypedDict  # <=py3.7

from packages.valory.contracts.gnosis_safe.contract import (
    GnosisSafeContract,
    SafeOperation,
)
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
    CalculateSpentGasPayload,
    GetJobsPayload,
    PathSelectionPayload,
    SwapAndDisburseRewardsPayload,
    TopUpPayload,
    UnbondingTxPayload,
    WaitingPayload,
    WorkTxPayload,
)
from packages.valory.skills.keep3r_job_abci.rounds import (
    ActivationRound,
    ApproveBondRound,
    AwaitTopUpRound,
    BondingRound,
    CalculateSpentGasRound,
    GetJobsRound,
    Keep3rJobAbciApp,
    PathSelectionRound,
    PerformWorkRound,
    SwapAndDisburseRewardsRound,
    SynchronizedData,
    UnbondingRound,
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

TO_WEI = 10**18


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
    def raise_on_failed_simulation(self) -> bool:
        """Return if we are raising on failed simulation, only applies if use_flashbots is True."""
        return self.context.params.raise_on_failed_simulation

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

    def get_bonded_amount(
        self, keeper_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[int]]:
        """Get bonded amount"""
        bonded_amount = yield from self.read_keep3r(
            "bondings",
            address=keeper_address,
            bonding_asset=bonding_asset,
        )
        if bonded_amount is None:
            # something went wrong
            return None
        return bonded_amount

    def should_unbond_k3pr(
        self, keeper_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[bool]]:
        """Check if we should unbond our k3pr."""
        bonded_amount = yield from self.get_bonded_amount(keeper_address, bonding_asset)
        if bonded_amount is None:
            # something went wrong
            return None
        wei_threshold = self.params.unbonding_threshold * TO_WEI
        return bonded_amount >= wei_threshold

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
            raise_on_failed_simulation=self.raise_on_failed_simulation,
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

        should_unbond = yield from self.should_unbond_k3pr(
            safe_address, self.params.k3pr_address
        )
        if should_unbond is None:
            # something went wrong
            return None
        # only if true we unbond, if false we continue with the rest of the logic
        if should_unbond:
            return self.transitions["UNBOND"].name

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


class UnbondingBehaviour(Keep3rJobBaseBehaviour):
    """A behaviour to unbond the rewarded K3PR."""

    matching_round: Type[AbstractRound] = UnbondingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            raw_tx = yield from self._build_unbond_tx()
            if raw_tx is None:
                yield from self.sleep(self.context.params.sleep_time)
                return
            unbonding_tx = yield from self.build_safe_raw_tx(cast(SafeTx, raw_tx))
            if not unbonding_tx:
                # something went wrong
                return
            self.context.logger.info(f"Unbonding tx: {unbonding_tx}")
            payload = UnbondingTxPayload(
                self.context.agent_address, unbonding_tx=unbonding_tx
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _build_unbond_tx(self) -> Generator[None, None, Optional[SafeTx]]:
        """Build unbond tx. This will unbond all the bonded K3PR amount."""
        safe_address = self.synchronized_data.safe_contract_address
        bonding_asset_address = self.context.params.k3pr_address
        bonded_amount = yield from self.get_bonded_amount(
            safe_address, bonding_asset_address
        )
        if bonded_amount is None:
            # something went wrong
            return None
        data_str = yield from self.read_keep3r(
            method="build_unbond_tx",
            bonded_asset_address=bonding_asset_address,
            amount=bonded_amount,
        )
        if data_str is None:
            # something went wrong
            return None
        data = bytes.fromhex(data_str[2:])
        safe_tx = SafeTx(
            data=data,
            to=self.keep3r_v2_contract_address,
            value=ZERO_ETH,
            gas=SAFE_GAS,
            gas_limit=AUTO_GAS_LIMIT,
        )
        return safe_tx


class CalculateSpentGasBehaviour(Keep3rJobBaseBehaviour):
    """A behaviour to check the amount of gas spent per user."""

    matching_round: Type[AbstractRound] = CalculateSpentGasRound
    _NO_EVENT: Dict = {}

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            address_to_gas_spent = yield from self._get_gas_spent()
            payload = CalculateSpentGasPayload(
                sender=self.context.agent_address,
                address_to_gas_spent=address_to_gas_spent,
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_gas_spent(self) -> Generator[None, None, str]:
        """Get the gas spent for the latest unbonding interval."""
        keeper_address = self.synchronized_data.safe_contract_address
        bonding_asset = self.params.k3pr_address
        latest_unbonding_event = yield from self._get_latest_unbonding_event(
            keeper_address, bonding_asset
        )
        if latest_unbonding_event is None or latest_unbonding_event == self._NO_EVENT:
            # something went wrong, the keeper MUST have unbonded if we have reached this point
            return CalculateSpentGasRound.ERROR_PAYLOAD

        latest_withdraw_event = yield from self._get_latest_withdrawal_event(
            keeper_address, bonding_asset
        )
        if latest_withdraw_event is None:
            # something went wrong
            return CalculateSpentGasRound.ERROR_PAYLOAD

        # we start from the block the block in which the last withdraw event happened, or from the first block if we have
        # never withdrawn
        from_block = (
            0
            if latest_withdraw_event == self._NO_EVENT
            else latest_withdraw_event["block_number"]
        )
        # we end at the block in which the last unbonding event happened
        to_block = latest_unbonding_event["block_number"]

        transactions = yield from self._get_safe_txs(
            keeper_address, from_block, to_block
        )
        if transactions is None:
            # something went wrong
            return CalculateSpentGasRound.ERROR_PAYLOAD

        transaction_hashes = [tx["tx_hash"] for tx in transactions]
        tx_sender_to_gas_spent = yield from self._tx_sender_to_gas_spent(
            transaction_hashes
        )
        if tx_sender_to_gas_spent is None:
            # something went wrong
            return CalculateSpentGasRound.ERROR_PAYLOAD
        tx_sender_to_gas_spent_str = json.dumps(tx_sender_to_gas_spent, sort_keys=True)
        return tx_sender_to_gas_spent_str

    def _get_latest_withdrawal_event(
        self, keeper_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[Dict]]:
        """Get withdrawal events"""
        withdrawal_events = yield from self.read_keep3r(
            "get_withdrawal_events",
            address=keeper_address,
            bonding_asset=bonding_asset,
        )
        if withdrawal_events is None:
            # something went wrong
            return None

        if len(withdrawal_events) == 0:
            # return the empty dict to indicate no withdraws
            return self._NO_EVENT

        # return the latest withdraw event
        # events are sorted by block number
        return withdrawal_events[-1]

    def _get_latest_unbonding_event(
        self, keeper_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[Dict]]:
        """Get unbonding events"""
        unbonding_events = yield from self.read_keep3r(
            "get_unbonding_events",
            address=keeper_address,
            bonding_asset=bonding_asset,
        )
        if unbonding_events is None:
            # something went wrong
            return None

        if len(unbonding_events) == 0:
            # return the empty dict to indicate no unbondings
            return self._NO_EVENT

        # return the latest unbonding event
        # events are sorted by block number
        return unbonding_events[-1]

    def _get_safe_txs(
        self, safe_address: str, from_block: int, to_block: int
    ) -> Generator[None, None, Optional[List[Dict]]]:
        """Get the safe txs."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=safe_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_safe_txs",
            from_block=from_block,
            to_block=to_block,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Failed to get safe txs: {contract_api_response}"
            )
            return None
        log_msg = f"`get_safe_txs` contract api response on {contract_api_response}"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(List[Dict], contract_api_response.state.body.get("data"))

    def _tx_sender_to_gas_spent(
        self, transaction_hashes: List[str]
    ) -> Generator[None, None, Optional[Dict[str, int]]]:
        """Get a mapping of tx senders to the amount of eth they've spent on gas for the given tx hashes."""
        tx_sender_to_gas_spent = yield from self.read_keep3r(
            "sender_to_amount_spent",
            transaction_hashes=transaction_hashes,
        )
        if tx_sender_to_gas_spent is None:
            # something went wrong
            return None

        return cast(Dict[str, int], tx_sender_to_gas_spent)


class SwapAndDisburseRewardsBehaviour(Keep3rJobBaseBehaviour):
    """SwapAndDisburseRewardsBehaviour"""

    matching_round: Type[AbstractRound] = SwapAndDisburseRewardsRound

    _ETH_INDEX = 0
    _K3PR_INDEX = 1

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            swap_and_disburse_tx = yield from self.get_tx()
            payload = SwapAndDisburseRewardsPayload(
                self.context.agent_address, swap_and_disburse_tx
            )

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def get_tx(self) -> Generator[None, None, str]:
        """
        Prepare the multisend transaction to execute.

        Required transactions to execute the swap and disburse:
        1. Withdraw the k3pr from the keep3r contract
        2. Approve the k3pr for the swap
        3. Swap the k3pr for eth
        4. Disburse the eth to the agents

        :returns: the multisend transaction, or error payload if something went wrong
        :yields: None
        """
        keeper_address = self.synchronized_data.safe_contract_address
        bonding_asset = self.context.params.bonding_asset
        k3pr_amount = yield from self._get_amount_to_swap(keeper_address, bonding_asset)
        if k3pr_amount is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        # get the minimum amount of eth we are willing to swap the k3pr for
        min_eth_amount = yield from self._get_eth_amount(k3pr_amount)
        if min_eth_amount is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        multisend_txs: List[Dict[str, Any]] = []
        # 1. get the withdraw transaction
        withdraw_tx = yield from self._get_withdraw_tx(
            self.keep3r_v2_contract_address, bonding_asset
        )
        if withdraw_tx is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        # 2. get the approve transaction
        approve_tx = yield from self._get_approve_tx(
            bonding_asset, self.params.curve_pool_contract_address, k3pr_amount
        )
        if approve_tx is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        # 3. get the swap transaction
        swap_tx = yield from self._get_swap_tx(
            self.params.curve_pool_contract_address, k3pr_amount, min_eth_amount
        )
        if swap_tx is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        # 4. get the agent disburse transactions
        address_to_gas_spent = self.synchronized_data.address_to_gas_spent
        address_to_eth = self._get_transfer_amounts(
            address_to_gas_spent, min_eth_amount
        )
        disburse_txs = self._get_disburse_txs(address_to_eth, min_eth_amount)
        if disburse_txs is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD

        multisend_txs.extend(disburse_txs)
        tx = yield from self._get_multisend_tx(multisend_txs)
        if tx is None:
            # something went wrong
            return SwapAndDisburseRewardsRound.ERROR_PAYLOAD
        return tx

    def _get_amount_to_swap(
        self, keeper_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[int]]:
        """Get the amount of K3PR to swap."""
        pending_unbonds = yield from self.read_keep3r(
            "pending_unbonds",
            address=keeper_address,
            bonding_asset=bonding_asset,
        )
        if pending_unbonds is None:
            # something went wrong
            return None

        # return the amount of K3PR to swap,
        # which should be all the available K3PR
        return pending_unbonds

    def _get_eth_amount(self, k3pr_amount: int) -> Generator[None, None, Optional[int]]:
        """Get the amount of eth we expect for the provided K3PR amount."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.context.params.curve_pool_contract_address,
            contract_id=str(CurvePoolContract.contract_id),
            contract_callable="get_dy_for_dx",
            dx=k3pr_amount,
            i=self._K3PR_INDEX,
            j=self._ETH_INDEX,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(f"Failed simulate_tx: {contract_api_response}")
            return None
        log_msg = f"`get_dy_for_dx` contract api response on {contract_api_response}"
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        return cast(int, contract_api_response.state.body.get("data", 0))

    def _get_swap_tx(
        self, pool_address: str, k3pr_amount: int, min_eth_amount: int
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Swap tx."""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=pool_address,
            contract_id=str(CurvePoolContract.contract_id),
            contract_callable="build_exchange_tx",
            dx=k3pr_amount,
            i=self._K3PR_INDEX,
            j=self._ETH_INDEX,
            min_dy=min_eth_amount,
        )
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Failed build_exchange_tx: {contract_api_response}"
            )
            return None
        log_msg = (
            f"`build_exchange_tx` contract api response on {contract_api_response}"
        )
        self.context.logger.info(f"{log_msg}: {contract_api_response}")
        data_str = cast(
            Optional[str], contract_api_response.state.body.get("data", False)
        )
        if data_str is None:
            # something went wrong
            return None

        data = bytes.fromhex(data_str[2:])
        # build a single tx
        single_tx = {
            "operation": MultiSendOperation.CALL,
            "to": pool_address,
            "value": ZERO_ETH,
            "data": HexBytes(data),
        }
        return single_tx

    def _get_withdraw_tx(
        self, keep3rV2_address: str, bonding_asset: str
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Withdraw tx."""
        withdraw_tx = yield from self.read_keep3r(
            "build_withdraw_tx",
            bonding_asset=bonding_asset,
        )
        if withdraw_tx is None:
            # something went wrong
            return None
        data = bytes.fromhex(withdraw_tx[2:])
        # build a single tx
        single_tx = {
            "operation": MultiSendOperation.CALL,
            "to": keep3rV2_address,
            "value": ZERO_ETH,
            "data": HexBytes(data),
        }
        return single_tx

    def _get_approve_tx(
        self, bonding_asset: str, spender: str, amount: int
    ) -> Generator[None, None, Optional[Dict[str, Any]]]:
        """Approve tx."""
        approve_tx = yield from self.build_approve_raw_tx(
            spender, bonding_asset, amount
        )
        if approve_tx is None:
            # something went wrong
            return None

        # build a single tx
        single_tx = {
            "operation": MultiSendOperation.CALL,
            "to": bonding_asset,
            "value": ZERO_ETH,
            "data": HexBytes(approve_tx["data"]),
        }
        return single_tx

    def _get_transfer_amounts(
        self, address_to_gas: Dict[str, int], eth_amount: int
    ) -> Dict[str, int]:
        """Get the transfer amounts for each address."""
        total_gas_spent = sum(address_to_gas.values())
        surplus = eth_amount - total_gas_spent
        if surplus <= 0:
            # there is no surplus, we divide the eth_amount based on the gas spent by each address
            self.context.logger.info(
                "There is no surplus, we divide the eth_amount based on the gas spent by each address."
            )
            return {
                address: int(eth_amount * gas_spent / total_gas_spent)
                for address, gas_spent in address_to_gas.items()
            }

        # agents get their share, the rest sits in the safe
        # agent_surplus_share defines the share of the surplus that goes to the agents
        agent_surplus_share: float = self.params.agent_surplus_share
        agent_surplus = int(surplus * agent_surplus_share)

        # there is a surplus, we divide the surplus equally among the agents
        surplus_per_agent = int(agent_surplus / len(address_to_gas))
        return {
            address: gas_spent + surplus_per_agent
            for address, gas_spent in address_to_gas.items()
        }

    def _get_disburse_txs(
        self, address_to_eth: Dict[str, int], eth_amount: int
    ) -> List[Dict[str, Any]]:
        """Get the transfer txs for each address."""
        transfer_amounts = self._get_transfer_amounts(address_to_eth, eth_amount)
        transfer_txs = []
        for address, amount in transfer_amounts.items():
            transfer_txs.append(
                {
                    "operation": MultiSendOperation.CALL,
                    "to": address,
                    "value": amount,
                    "data": b"",
                }
            )
        return transfer_txs

    def _get_safe_tx_hash(self, data: bytes) -> Generator[None, None, Optional[str]]:
        """Prepares and returns the safe tx hash."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=self.params.multisend_address,  # we send the tx to the multisend address
            value=ZERO_ETH,
            data=data,
            safe_tx_gas=SAFE_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
        )

        if response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(
                f"Couldn't get safe hash. "
                f"Expected response performative {ContractApiMessage.Performative.STATE.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response hash
        tx_hash = cast(str, response.state.body["tx_hash"])[2:]
        return tx_hash

    def _get_multisend_tx(
        self,
        multi_send_txs: List[Dict[str, Any]],
    ) -> Generator[None, None, Optional[str]]:
        """Get the multisend tx."""
        response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.params.multisend_address,
            contract_id=str(MultiSendContract.contract_id),
            contract_callable="get_tx_data",
            multi_send_txs=multi_send_txs,
        )
        if response.performative != ContractApiMessage.Performative.RAW_TRANSACTION:
            self.context.logger.error(
                f"Couldn't compile the multisend tx. "
                f"Expected response performative {ContractApiMessage.Performative.RAW_TRANSACTION.value}, "  # type: ignore
                f"received {response.performative.value}."
            )
            return None

        # strip "0x" from the response
        multisend_data_str = cast(str, response.raw_transaction.body["data"])[2:]
        tx_data = bytes.fromhex(multisend_data_str)
        tx_hash = yield from self._get_safe_tx_hash(tx_data)
        if tx_hash is None:
            # something went wrong
            return None

        payload_data = hash_payload_to_hex(
            safe_tx_hash=tx_hash,
            ether_value=ZERO_ETH,
            safe_tx_gas=SAFE_GAS,
            operation=SafeOperation.DELEGATE_CALL.value,
            to_address=self.params.multisend_address,
            data=tx_data,
        )
        return payload_data


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


class PerformWorkBehaviour(Keep3rJobBaseBehaviour):
    """PerformWorkBehaviour"""

    matching_round: Type[AbstractRound] = PerformWorkRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            work_tx = yield from self._get_work_tx()
            if work_tx is None:
                # something went wrong, just return to repeat
                return
            payload = WorkTxPayload(self.context.agent_address, work_tx)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_work_tx(self) -> Generator[None, None, Optional[str]]:
        """
        Get the work tx payload.

        :returns: the work tx payload or a special payload if no workable job is found.
        :yield: None
        """
        job_address = yield from self._get_workable_job()
        if job_address is None:
            # no workable job
            self.context.logger.info("No workable job found.")
            return PerformWorkRound.NO_WORKABLE_JOB_PAYLOAD

        self.context.logger.info(f"{job_address} is workable.")
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
            # something went wrong
            yield from self.sleep(self.context.params.sleep_time)
            return None
        safe_address = self.synchronized_data.safe_contract_address
        raw_tx = yield from self.build_work_raw_tx(
            job_address,
            contract_public_id,
            safe_address,
            **off_chain_data,
        )
        if raw_tx is None:
            # something went wrong
            yield from self.sleep(self.context.params.sleep_time)
            return None
        tx_data = cast(bytes, raw_tx.get("data"))
        simulation_ok = yield from self.simulate_tx(
            job_address,
            contract_public_id,
            tx_data,
            safe_address,
        )
        if simulation_ok is None:
            # something went wrong while simulating
            yield from self.sleep(self.context.params.sleep_time)
            return None
        if not simulation_ok:
            # simulation failed, i.e. a bad tx
            self.context.logger.info(
                f"Simulating a work tx for job {job_address} failed. "
                f"Tx data: {tx_data.hex()}."
            )
            return PerformWorkRound.SIMULATION_FAILED_PAYLOAD

        work_tx = yield from self.build_safe_raw_tx(raw_tx)
        if work_tx is None:
            # something went wrong
            yield from self.sleep(self.context.params.sleep_time)
            return None

        return work_tx

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

    def _get_workable_job(self) -> Generator[None, None, Optional[str]]:
        """Get the workable jobs."""
        job_list = self.synchronized_data.job_list
        job_list.sort()
        for job in job_list:
            is_workable = yield from self._is_workable(job)
            if is_workable:
                return job
        return None


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
        UnbondingBehaviour,  # type: ignore
        WaitingBehaviour,  # type: ignore
        ActivationBehaviour,  # type: ignore
        GetJobsBehaviour,  # type: ignore
        PerformWorkBehaviour,  # type: ignore
        AwaitTopUpBehaviour,  # type: ignore
    }
