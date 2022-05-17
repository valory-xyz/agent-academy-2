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

"""This module contains the data classes for the simple ABCI application."""

from abc import ABC
from enum import Enum
from typing import Dict, Optional, Tuple, Type, cast

from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsWorkablePayload,
    JobSelectionPayload,
    TXHashPayload,
    TransactionType,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)


class Event(Enum):
    """Event enumeration for the simple abci demo."""

    DONE = "done"
    NOT_WORKABLE = "not_workable"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(
            str,
            self.db.get_strict("most_voted_tx_hash"),
        )

    @property
    def job_selection(self) -> str:
        """Get the job_selection."""
        return cast(
            str,
            self.db.get_strict("job_selection"),
        )


class Keep3rJobAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the simple abci skill."""

    @property
    def period_state(self) -> BasePeriodState:
        """Return the period state."""
        return cast(BasePeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[BasePeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class IsWorkableRound(CollectSameUntilThresholdRound, Keep3rJobAbstractRound):
    """Check whether the keep3r job contract is workable."""

    round_id = "is_workable"
    allowed_tx_type = IsWorkablePayload.transaction_type
    payload_attribute = "is_workable"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                is_workable=self.most_voted_payload,
            )
            is_workable = self.most_voted_payload
            if is_workable:
                return state, Event.DONE
            return state, Event.NOT_WORKABLE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class JobSelectionRound(CollectSameUntilThresholdRound, Keep3rJobAbstractRound):
    """Handle the keep3r job selection."""

    round_id = "job_selection"
    allowed_tx_type = JobSelectionPayload.transaction_type
    payload_attribute = "job_selection"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            job_selection = self.most_voted_payload
            state = self.period_state.update(job_selection=job_selection)
            if job_selection:
                state = self.period_state.update(job_selection=job_selection)
                return state, Event.DONE
            return state, Event.NOT_WORKABLE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class PrepareTxRound(CollectSameUntilThresholdRound, Keep3rJobAbstractRound):
    """A round in a which tx hash is prepared is selected"""

    round_id = "prepare_tx"
    allowed_tx_type = TXHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class FinishedPrepareTxRound(DegenerateRound, ABC):
    """A round that represents the transition to the RandomnessTransactionSubmissionRound"""

    round_id = "finished_prepare_tx_round"


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "failed_round"


class NothingToDoRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "nothing_to_do"


class Keep3rJobAbciApp(AbciApp[Event]):
    """PrepareTxAbciApp

    Initial round: PrepareTxRound

    Initial states: {PrepareTxRound}

    Transition states:
        0. PrepareTxRound
            - done: 1.
            - reset timeout: 2.
            - no majority: 2.
        1. FinishedTransactionSubmissionRound
        2. FailedRound

    Final states: {}

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = JobSelectionRound
    transition_function: AbciAppTransitionFunction = {
        JobSelectionRound: {
            Event.DONE: IsWorkableRound,
            Event.NOT_WORKABLE: NothingToDoRound,
            Event.RESET_TIMEOUT: NothingToDoRound,
            Event.NO_MAJORITY: NothingToDoRound,
        },
        IsWorkableRound: {
            Event.DONE: PrepareTxRound,
            Event.NOT_WORKABLE: NothingToDoRound,
            Event.RESET_TIMEOUT: IsWorkableRound,
            Event.NO_MAJORITY: IsWorkableRound,
        },
        PrepareTxRound: {
            Event.DONE: FinishedPrepareTxRound,
            Event.RESET_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: FailedRound,
        },
        NothingToDoRound: {},
        FinishedPrepareTxRound: {},
        FailedRound: {},
    }
    final_states = {FinishedPrepareTxRound, FailedRound, NothingToDoRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
