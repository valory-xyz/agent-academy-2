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
from typing import Generator, Optional, Set, Type, cast

from packages.gabrielfu.contracts.keep3r_job.contract import Keep3rJobContract
from packages.keep3r_co.skills.keep3r_job.models import Params
from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsWorkablePayload,
    JobSelectionPayload,
    TXHashPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    IsWorkableRound,
    JobSelectionRound,
    Keep3rJobAbciApp,
    PeriodState,
    PrepareTxRound,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)


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
            self.context.logger.info(
                f"Interacting with Job contract at {self.context.params.job_contract_address}"
            )
            job_selection = self._job_selection()
            if job_selection is None:
                job_selection = False
            payload = JobSelectionPayload(self.context.agent_address, job_selection)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Job contract is selected {self.context.params.job_contract_address}: {job_selection}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _job_selection(self) -> str:
        next_job_ix = self.period_state.job_ix + 1
        next_job = self.context.params.job_contracts[next_job_ix]
        self.period_state.job_ix = next_job_ix
        return next_job


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
                f"Interacting with Job contract at {self.context.params.job_contract_address}"
            )
            is_workable = yield from self._get_workable()
            if is_workable is None:
                is_workable = False
            payload = IsWorkablePayload(self.context.agent_address, is_workable)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Job contract is workable {self.context.params.job_contract_address}: {is_workable}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_workable(self) -> Generator:
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.context.params.job_contract_address,
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

            tx_hash = yield from self._get_raw_work_transaction()
            payload = TXHashPayload(self.context.agent_address, tx_hash)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_raw_work_transaction(self) -> Generator[None, None, Optional[str]]:
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            contract_address=self.context.params.job_contract_address,
            contract_id=str(Keep3rJobContract.contract_id),
            contract_callable="get_workable",
        )
        if (
                contract_api_response.performative
                != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("Get work transaction unsuccessful!")
            return None
        tx_hash = cast(
            str, contract_api_response.raw_transaction.body.pop("hash")
        )

        return tx_hash


class Keep3rJobRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the preparetx abci app."""

    initial_state_cls = PrepareTxBehaviour  # type: ignore
    abci_app_cls = Keep3rJobAbciApp  # type: ignore
    behaviour_states: Set[Type[Keep3rJobAbciBaseState]] = {  # type: ignore
        JobSelectionBehaviour,  # type: ignore
        IsWorkableBehaviour,  # type: ignore
        PrepareTxBehaviour,  # type: ignore

    }
