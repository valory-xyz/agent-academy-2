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
from typing import Any, Dict, Generator, List, Optional, Set, Type, cast

from packages.keep3r_co.skills.keep3r_job.models import Params
from packages.keep3r_co.skills.keep3r_job.payloads import (
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    PathSelectionPayload,
    WorkTxPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    ActivationRound,
    AwaitTopUpRound,
    BondingRound,
    Event,
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

    @property
    def current_job_contract(self) -> Optional[str]:
        """Get current job contract address"""
        if not self.context.params.job_contract_addresses:
            return None
        addresses = self.context.params.job_contract_addresses
        job_ix = self.synchronized_data.period_count % len(addresses)
        return self.context.params.job_contract_addresses[job_ix]


class PathSelectionBehaviour(Keep3rJobBaseBehaviour):
    """PathSelectionBehaviour"""

    behaviour_id: str = "path_selection"
    matching_round: Type[AbstractRound] = PathSelectionRound
    transitions = PathSelectionRound.transitions

    def read_keep3r_v1(self, method: str, **kwargs: Any) -> Generator[None, None, Any]:
        """Read Keep3r V1 contract state"""

        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.current_job_contract,
            contract_id=str(Keep3rV1Contract.contract_id),
            contract_callable=method,
            **kwargs,
        )
        return contract_api_response.state.body.get("data")

    def is_bonded_keep3r(self, bond_time: int) -> Generator[None, None, bool]:
        """Is bonded keep3r"""

        bond = yield from self.read_keep3r_v1("BOND")  # contract parameter
        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_block",
            block_identifier="latest",
        )
        latest_block = cast(Dict, ledger_api_response.state.body.get("data"))
        return latest_block["timestamp"] > bond_time + bond

    def has_sufficient_funds(self, address: str) -> Generator[None, None, bool]:
        """Has sufficient funds"""

        ledger_api_response = yield from self.get_ledger_api_response(
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_callable="get_balance",
            account=address,
        )
        balance = cast(int, ledger_api_response.state.body.get("data"))
        return balance >= cast(int, self.context.params.threshold)

    def select_path(self) -> Event:
        """Select path to traverse"""

        address = self.synchronized_data.safe_contract_address
        blacklisted = self.read_keep3r_v1("blacklisted", address=address)
        if blacklisted:  # pylint: disable=using-constant-test
            return self.transitions["BLACKLISTED"]
        sufficient_funds = self.has_sufficient_funds(address)
        if not sufficient_funds:
            return self.transitions["INSUFFICIENT_FUNDS"]
        bond_time = cast(int, self.read_keep3r_v1("bondings", address=address))
        if not bond_time:
            return self.transitions["NOT_BONDED"]
        bonded_keeper = self.is_bonded_keep3r(bond_time)
        if not bonded_keeper:
            return self.transitions["NOT_ACTIVATED"]
        return self.transitions["HEALTHY"]

    def async_act(self) -> Generator:
        """Behaviour to select the path to traverse"""

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            path = self.select_path()
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


class WaitingBehaviour(Keep3rJobBaseBehaviour):
    """WaitingBehaviour"""

    behaviour_id: str = "waiting"
    matching_round: Type[AbstractRound] = WaitingRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


class ActivationBehaviour(Keep3rJobBaseBehaviour):
    """ActivationBehaviour"""

    behaviour_id: str = "activation"
    matching_round: Type[AbstractRound] = ActivationRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


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
            job_contract = self.current_job_contract
            payload = JobSelectionPayload(self.context.agent_address, job_contract)
            self.context.logger.info(f"Job contract selected : {job_contract}")

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class IsWorkableBehaviour(Keep3rJobBaseBehaviour):
    """IsWorkableBehaviour"""

    behaviour_id: str = "is_workable"
    matching_round: Type[AbstractRound] = IsWorkableRound

    def async_act(self) -> Generator:
        """
        Behaviour to get whether job is workable.

        is workable payload is shared between participants.
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            self.context.logger.info(
                f"Interacting with Job contract at {self.current_job_contract}"
            )
            is_workable = yield from self._get_workable()
            if is_workable is None:
                is_workable = False
            payload = IsWorkablePayload(self.context.agent_address, is_workable)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            self.context.logger.info(
                f"Job contract is workable {self.current_job_contract}: {is_workable}"
            )
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_workable(self) -> Generator:
        """Get workable jobs from contract"""
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.current_job_contract,
            contract_id=str(Keep3rTestJobContract.contract_id),
            contract_callable="get_workable",
        )
        is_workable = contract_api_response.state.body.get("data")
        return is_workable


class IsProfitableBehaviour(Keep3rJobBaseBehaviour):
    """IsProfitableBehaviour"""

    behaviour_id: str = "is_profitable"
    matching_round: Type[AbstractRound] = IsProfitableRound

    def async_act(self) -> Generator:
        """Do the action

        Steps:
        - Call the contract to get the rewardMultiplier
        - Check if the job is profitable given the current rewardMultiplier
        - Set Payload accordingly and send transaction, then end the round.
        """

        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            reward_multiplier = yield from self.rewardMultiplier()
            if reward_multiplier is None:
                raise RuntimeError("Contract call has failed")

            # TODO: compute a more meaningful profitability measure
            if reward_multiplier > self.context.params.profitability_threshold:
                payload = IsProfitablePayload(self.context.agent_address, True)
            else:
                payload = IsProfitablePayload(self.context.agent_address, False)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            self.context.logger.info(f"Safe transaction hash: {reward_multiplier}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def rewardMultiplier(self) -> Generator:
        """Calls the contract to get the reward multiplier for the job."""

        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.current_job_contract,
            contract_id=str(Keep3rTestJobContract.contract_id),
            contract_callable="rewardMultiplier",
        )
        if (
            contract_api_response.performative != ContractApiMessage.Performative.STATE
        ):  # pragma: nocover
            self.context.logger.warning("Get reward multiplier unsuccessful!")
            return None

        reward_multiplier = cast(
            int, contract_api_response.state.body.pop("rewardMultiplier")
        )
        return reward_multiplier


class PerformWorkBehaviour(Keep3rJobBaseBehaviour):
    """PerformWorkBehaviour"""

    behaviour_id: str = "perform_work"
    matching_round: Type[AbstractRound] = PerformWorkRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - If the agent is the designated deployer, then prepare the deployment
          transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        with self.context.benchmark_tool.measure(self.behaviour_id).local():
            work_tx = yield from self._get_raw_work_transaction_hash()
            if not work_tx:
                return
            payload = WorkTxPayload(self.context.agent_address, work_tx)

        with self.context.benchmark_tool.measure(self.behaviour_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_raw_work_transaction_hash(self) -> Generator[None, None, Optional[str]]:

        job_contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_id=str(Keep3rTestJobContract.contract_id),
            contract_callable="work",
            contract_address=self.current_job_contract,
            sender_address=self.context.agent_address,
        )

        if (
            job_contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("get raw work transaction unsuccessful!")
            return None

        tx_params = job_contract_api_response.raw_transaction.body
        safe_contract_address = self.synchronized_data.safe_contract_address

        safe_contract_api_msg = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=safe_contract_address,
            contract_id=str(GnosisSafeContract.contract_id),
            contract_callable="get_raw_safe_transaction_hash",
            to_address=tx_params["to_address"],
            value=tx_params["ether_value"],
            data=tx_params["data"],
            safe_tx_gas=tx_params["safe_tx_gas"],
        )
        if (
            safe_contract_api_msg.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("Get work transaction hash unsuccessful!")
            return None
        tx_hash = cast(str, job_contract_api_response.raw_transaction.body.pop("hash"))

        return tx_hash


class AwaitTopUpBehaviour(Keep3rJobBaseBehaviour):
    """AwaitTopUpBehaviour"""

    behaviour_id: str = "await_top_up"
    matching_round: Type[AbstractRound] = AwaitTopUpRound

    def async_act(self) -> Generator:
        """Do the act, supporting asynchronous execution."""


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
