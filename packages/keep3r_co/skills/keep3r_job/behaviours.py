# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the behaviours for the 'keep3r_job' skill."""

from abc import ABC
from typing import Any, Dict, Generator, List, Optional, Set, Type, TypedDict, cast

from packages.keep3r_co.skills.keep3r_job.models import Params
from packages.keep3r_co.skills.keep3r_job.payloads import (
    ActivationTxPayload,
    BondingTxPayload,
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    PathSelectionPayload,
    TopUpPayload,
    WaitingPayload,
    WorkTxPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    ActivationRound,
    AwaitTopUpRound,
    BondingRound,
    GetJobsRound,
    IsProfitableRound,
    IsWorkableRound,
    JobSelectionRound,
    Keep3rJobAbciApp,
    PathSelectionRound,
    PerformWorkRound,
    SynchronizedData,
    WaitingRound,
)
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.contracts.keep3r_test_job.contract import Keep3rTestJobContract
from packages.valory.contracts.keep3r_v1.contract import Keep3rV1Contract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbstractRound
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseBehaviour,
)


RawTx = TypedDict(
    "RawTx",
    {
        "chainId": int,
        "data": str,
        "from": str,
        "gas": int,
        "maxFeePerGas": int,
        "maxPriorityFeePerGas": int,
        "nonce": int,
        "to": str,
        "value": int,
    },
)


class Keep3rJobBaseBehaviour(BaseBehaviour, ABC):
    """Base state behaviour for the simple abci skill."""

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

    def _call_keep3r_v1(self, **kwargs: Any) -> Generator[None, None, ContractApiMessage]:
        """Helper method"""
        contract_api_response = yield from self.get_contract_api_response(
            contract_address=self.keep3r_v1_contract_address,
            contract_id=str(Keep3rV1Contract.contract_id),
            **kwargs,
        )
        self.context.logger.info(f"Keep3r v1 response: {contract_api_response}")
        return contract_api_response

    def read_keep3r_v1(self, method: str, **kwargs: Any) -> Generator[None, None, Any]:
        """Read Keep3r V1 contract state"""

        kwargs['performative'] = ContractApiMessage.Performative.GET_STATE
        kwargs["contract_callable"] = method
        contract_api_response = yield from self._call_keep3r_v1(**kwargs)
        if contract_api_response.performative != ContractApiMessage.Performative.STATE:
            self.context.logger.error(f"Failed read_keep3r_v1: {contract_api_response}")
            return None
        return contract_api_response.state.body.get("data")

    def build_keep3r_raw_tx(
        self, method: str, **kwargs: Any
    ) -> Generator[None, None, Optional[RawTx]]:
        """Build Keep3r V1 raw transaction"""

        kwargs["performative"] = ContractApiMessage.Performative.GET_RAW_TRANSACTION
        kwargs["contract_callable"] = method
        contract_api_response = yield from self._call_keep3r_v1(**kwargs)
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self.context.logger.error(f"Failed build_keep3r_v1_raw_tx: {method}")
            return None
        return cast(RawTx, contract_api_response.raw_transaction.body.get("data"))

    def has_bonded(self, bond_time: int) -> Generator[None, None, bool]:
        """Check if bonding is completed"""

        bond = yield from self.read_keep3r_v1("BOND")  # contract parameter
        if bond is None:
            self.context.logger.error("Failed keep3r v1 BOND call")
            return False
        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_block",
            block_identifier="latest",
        )
        if ledger_api_response.performative != LedgerApiMessage.Performative.STATE:
            self.context.logger.error(f"Failed has_bonded: {ledger_api_response}")
            return False
        latest_block = cast(Dict, ledger_api_response.state.body.get("data"))
        remaining_time = bond_time + bond - latest_block["timestamp"]
        self.context.logger.info(f"Remaining bond time: {remaining_time}")
        return remaining_time <= 0

    def has_sufficient_funds(self, address: str) -> Generator[None, None, bool]:
        """Has sufficient funds"""

        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_balance",
            account=address,
        )
        if ledger_api_response.performative != LedgerApiMessage.Performative.STATE:
            return False  # transition to await top-up round
        balance = cast(int, ledger_api_response.state.body.get("data"))
        self.context.logger.info(f"balance: {balance / 10 ** 18} ETH")
        return balance >= cast(int, self.context.params.insufficient_funds_threshold)

    def build_safe_raw_tx(
        self,
        tx_params: Dict[str, Any],
    ) -> Generator[None, None, Optional[str]]:
        """Build safe raw tx hash"""

        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.synchronized_data.safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
        )
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self.context.logger.warning("build_safe_raw_tx unsuccessful!")
            return None
        tx_hash = cast(str, contract_api_response.raw_transaction.body.pop("hash"))
        return tx_hash


class PathSelectionBehaviour(Keep3rJobBaseBehaviour):
    """PathSelectionBehaviour"""

    behaviour_id: str = "path_selection"
    matching_round: Type[AbstractRound] = PathSelectionRound
    transitions = PathSelectionRound.transitions

    def select_path(self) -> Generator[None, None, Any]:
        """Select path to traverse"""

        address = self.synchronized_data.safe_contract_address
        blacklisted = yield from self.read_keep3r_v1("blacklist", address=address)
        if blacklisted:
            return self.transitions["BLACKLISTED"].name
        sufficient_funds = yield from self.has_sufficient_funds(address)
        if not sufficient_funds:
            return self.transitions["INSUFFICIENT_FUNDS"].name
        bond_time = yield from self.read_keep3r_v1("bondings", address=address)
        if not bond_time:
            return self.transitions["NOT_BONDED"].name
        bonded_keeper = yield from self.has_bonded(bond_time)
        if not bonded_keeper:
            return self.transitions["NOT_ACTIVATED"].name
        return self.transitions["HEALTHY"].name

    def async_act(self) -> Generator:
        """Behaviour to select the path to traverse"""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            path = yield from self.select_path()
            payload = PathSelectionPayload(self.context.agent_address, path)
            self.context.logger.info(f"Selected path: {path}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class BondingBehaviour(Keep3rJobBaseBehaviour):
    """BondingBehaviour"""

    behaviour_id: str = "bonding"
    matching_round: Type[AbstractRound] = BondingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            contract_api_response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=self.keep3r_v1_contract_address,
                contract_id=str(Keep3rV1Contract.contract_id),
                contract_callable="build_bond_tx",
            )
            state_performative = ContractApiMessage.Performative.STATE
            if contract_api_response.performative != state_performative:
                log_msg = "Failed build_bond_tx"
                self.context.logger.error(f"{log_msg}: {contract_api_response}")
                yield from self.sleep(self.context.params.sleep_time)
                return

            bonding_tx = cast(str, contract_api_response.state.body.get("data"))
            payload = BondingTxPayload(
                self.context.agent_address, bonding_tx=bonding_tx
            )
            self.context.logger.info(f"Bonding raw tx: {bonding_tx}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class WaitingBehaviour(Keep3rJobBaseBehaviour):
    """WaitingBehaviour"""

    behaviour_id: str = "waiting"
    matching_round: Type[AbstractRound] = WaitingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            address = self.synchronized_data.safe_contract_address
            bond_time = yield from self.read_keep3r_v1("bondings", address=address)
            if bond_time is None:
                log_msg = "Failed to check `bondings` on Keep3rV1 contract"
                self.context.logger.error(log_msg)
                yield from self.sleep(self.context.params.sleep_time)
                return
            done_waiting = yield from self.has_bonded(bond_time)
            self.context.logger.info(f"Done waiting: {done_waiting}")
            if not done_waiting:
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

    behaviour_id: str = "activation"
    matching_round: Type[AbstractRound] = ActivationRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            contract_api_response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=self.keep3r_v1_contract_address,
                contract_id=str(Keep3rV1Contract.contract_id),
                contract_callable="build_activation_tx",
            )
            activation_tx = cast(str, contract_api_response.state.body.get("data"))
            payload = ActivationTxPayload(
                self.context.agent_address, activation_tx=activation_tx
            )
            self.context.logger.info(f"Activation raw tx: {activation_tx}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class GetJobsBehaviour(Keep3rJobBaseBehaviour):
    """GetJobsBehaviour"""

    behaviour_id: str = "get_jobs"
    matching_round: Type[AbstractRound] = GetJobsRound

    def async_act(self) -> Generator:
        """Behaviour to get the current job listing"""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            contract_api_response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,
                contract_address=self.keep3r_v1_contract_address,
                contract_id=str(Keep3rV1Contract.contract_id),
                contract_callable="get_jobs",
            )
            job_list = cast(List[str], contract_api_response.state.body.get("data"))
            payload = GetJobsPayload(self.context.agent_address, job_list=job_list)
            self.context.logger.info(f"Job list retrieved: {job_list}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class JobSelectionBehaviour(Keep3rJobBaseBehaviour):
    """JobSelectionBehaviour"""

    behaviour_id: str = "job_selection"
    matching_round: Type[AbstractRound] = JobSelectionRound

    def async_act(self) -> Generator:
        """
        Behaviour to get whether job is selected.

        job selection payload is shared between participants.
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            if not self.synchronized_data.job_list:
                current_job = None
            else:
                addresses = self.synchronized_data.job_list
                period_count = self.synchronized_data.period_count
                job_ix = period_count % len(addresses)
                current_job = addresses[job_ix]
            payload = JobSelectionPayload(self.context.agent_address, current_job)
            self.context.logger.info(f"Job contract selected: {current_job}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class IsWorkableBehaviour(Keep3rJobBaseBehaviour):
    """IsWorkableBehaviour"""

    behaviour_id: str = "is_workable"
    matching_round: Type[AbstractRound] = IsWorkableRound

    def async_act(self) -> Generator:
        """Behaviour to get whether job is workable."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            current_job = self.synchronized_data.current_job
            contract_api_response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_address=current_job,
                contract_id=str(Keep3rTestJobContract.contract_id),  # TODO
                contract_callable="workable",
            )
            log_msg = f"`workable` contract api response on {current_job}"
            self.context.logger.info(f"{log_msg}: {contract_api_response}")
            is_workable = bool(contract_api_response.state.body.get("data"))
            payload = IsWorkablePayload(self.context.agent_address, is_workable)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class IsProfitableBehaviour(Keep3rJobBaseBehaviour):
    """IsProfitableBehaviour"""

    behaviour_id: str = "is_profitable"
    matching_round: Type[AbstractRound] = IsProfitableRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            current_job = self.synchronized_data.current_job
            reward = yield from self.read_keep3r_v1("credits", address=current_job)
            is_profitable = reward >= self.context.params.profitability_threshold
            self.context.logger.info(f"reward: {reward}, profitable: {is_profitable}")
            payload = IsProfitablePayload(self.context.agent_address, is_profitable)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class PerformWorkBehaviour(Keep3rJobBaseBehaviour):
    """PerformWorkBehaviour"""

    behaviour_id: str = "perform_work"
    matching_round: Type[AbstractRound] = PerformWorkRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():

            address = self.synchronized_data.safe_contract_address
            contract_api_response = yield from self.get_contract_api_response(
                performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
                contract_id=str(Keep3rTestJobContract.contract_id),
                contract_callable="build_work_tx",
                contract_address=self.synchronized_data.current_job,
                address=address,
            )
            work_tx = cast(str, contract_api_response.state.body.get("data"))
            payload = WorkTxPayload(self.context.agent_address, work_tx)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class AwaitTopUpBehaviour(Keep3rJobBaseBehaviour):
    """AwaitTopUpBehaviour"""

    behaviour_id: str = "await_top_up"
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
        PathSelectionBehaviour,  # type: ignore
        BondingBehaviour,  # type: ignore
        WaitingBehaviour,  # type: ignore
        ActivationBehaviour,  # type: ignore
        GetJobsBehaviour,  # type: ignore
        JobSelectionBehaviour,  # type: ignore
        IsWorkableBehaviour,  # type: ignore
        IsProfitableBehaviour,  # type: ignore
        PerformWorkBehaviour,  # type: ignore
        AwaitTopUpBehaviour,  # type: ignore
    }
