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
from typing import Any, Generator, Optional, Set, Type, cast

from packages.gabrielfu.contracts.keep3r_job.contract import Keep3rJobContract
from packages.keep3r_co.skills.keep3r_job.models import Params
from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    SafeExistencePayload,
    TXHashPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    CheckSafeExistenceRound,
    IsProfitableRound,
    IsWorkableRound,
    JobSelectionRound,
    Keep3rJobAbciApp,
    PeriodState,
    PrepareTxRound,
)
from packages.valory.contracts.gnosis_safe.contract import GnosisSafeContract
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)


class CheckSafeExistenceBehaviour(BaseState):
    """Check Safe contract existence."""

    state_id = "check_safe_existence"
    matching_round = CheckSafeExistenceRound

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Check if any safe contract is deployed already
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            exists = self.safe_contract_exists()
            payload = SafeExistencePayload(self.context.agent_address, exists)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def safe_contract_exists(self) -> bool:
        """Check Contract deployment verification."""

        if self.period_state.safe_contract_address is None:  # pragma: nocover
            self.context.logger.warning("Safe contract has not been deployed!")
            return False

        return True


class Keep3rJobAbciBaseState(BaseState, ABC):
    """Base state behaviour for the simple abci skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

    @property
    def current_job_contract(self) -> Optional[str]:
        """Get current job contract address"""
        if not self.context.params.job_contract_addresses:
            return None
        addresses = self.context.params.job_contract_addresses
        job_ix = self.period_state.period_count % len(addresses)
        return self.context.params.job_contract_addresses[job_ix]


class JobSelectionBehaviour(Keep3rJobAbciBaseState):
    """Check whether the job contract is selected."""

    state_id = "job_selection"
    matching_round = JobSelectionRound

    def async_act(self) -> Generator:
        """
        Behaviour to get whether job is selected.

        job selection payload is shared between participants.
        """
        with self.context.benchmark_tool.measure(self.state_id).local():
            job_selection = self.current_job_contract
            payload = JobSelectionPayload(self.context.agent_address, job_selection)
            self.context.logger.info(f"Job contract selected : {job_selection}")

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()


class IsWorkableBehaviour(Keep3rJobAbciBaseState):
    """Check whether the job contract is workable."""

    state_id = "is_workable"
    matching_round = IsWorkableRound

    def async_act(self) -> Generator:
        """
        Behaviour to get whether job is workable.

        is workable payload is shared between participants.
        """
        with self.context.benchmark_tool.measure(self.state_id).local():
            self.context.logger.info(
                f"Interacting with Job contract at {self.current_job_contract}"
            )
            is_workable = yield from self._get_workable()
            if is_workable is None:
                is_workable = False
            payload = IsWorkablePayload(self.context.agent_address, is_workable)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
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
            contract_id=str(Keep3rJobContract.contract_id),
            contract_callable="get_workable",
        )
        is_workable = contract_api_response.state.body.get("data")
        return is_workable


class PrepareTxBehaviour(Keep3rJobAbciBaseState):
    """Deploy Safe."""

    state_id = "prepare_tx"
    matching_round = PrepareTxRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - If the agent is the designated deployer, then prepare the deployment
          transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        with self.context.benchmark_tool.measure(self.state_id).local():

            tx_hash = yield from self._get_raw_work_transaction_hash()
            payload = TXHashPayload(self.context.agent_address, tx_hash)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_raw_work_transaction_hash(self) -> Generator[None, None, Optional[str]]:

        job_contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_id=str(Keep3rJobContract.contract_id),
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
        safe_contract_address = self.context.params.period_setup_params.get(
            "safe_contract_address"
        )

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


class IsProfitableBehaviour(Keep3rJobAbciBaseState):
    """Checks if job is profitable."""

    state_id = "get_is_profitable"
    matching_round = IsProfitableRound

    def async_act(self) -> Generator:
        """Do the action

        Steps:
        - Call the contract to get the rewardMultiplier
        - Check if the job is profitable given the current rewardMultiplier
        - Set Payload accordingly and send transaction, then end the round.
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            reward_multiplier = yield from self.rewardMultiplier()
            if reward_multiplier is None:
                raise RuntimeError("Contract call has failed")

            # TODO: compute a more meaningful profitability measure
            if reward_multiplier > self.context.params.profitability_threshold:
                payload = IsProfitablePayload(self.context.agent_address, True)
            else:
                payload = IsProfitablePayload(self.context.agent_address, False)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Safe transaction hash: {reward_multiplier}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def rewardMultiplier(self) -> Generator:
        """Calls the contract to get the rewardMultiplier for the job."""

        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,
            contract_address=self.current_job_contract,
            contract_id=str(Keep3rJobContract.contract_id),
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


class Keep3rJobRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the preparetx abci app."""

    initial_state_cls = PrepareTxBehaviour  # type: ignore
    abci_app_cls = Keep3rJobAbciApp  # type: ignore
    behaviour_states: Set[Type[Keep3rJobAbciBaseState]] = {  # type: ignore
        CheckSafeExistenceBehaviour,  # type: ignore
        JobSelectionBehaviour,  # type: ignore
        IsWorkableBehaviour,  # type: ignore
        IsProfitableBehaviour,  # type: ignore
        PrepareTxBehaviour,  # type: ignore
    }
