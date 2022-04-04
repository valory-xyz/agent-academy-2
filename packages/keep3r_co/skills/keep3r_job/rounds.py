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
import struct
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, List, Optional, Sequence, Tuple, Type, cast, Mapping

from packages.keep3r_co.skills.keep3r_job.models import SharedState
from packages.keep3r_co.skills.keep3r_job.payloads import TXHashPayload, TransactionType
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
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


def encode_float(value: float) -> bytes:  # pragma: nocover
    """Encode a float value."""
    return struct.pack("d", value)


def rotate_list(my_list: list, positions: int) -> List[str]:
    """Rotate a list n positions."""
    return my_list[positions:] + my_list[:positions]


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """


class SimpleABCIAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the simple abci skill."""

    @property
    def period_state(self) -> SharedState:
        """Return the period state."""
        return cast(SharedState, self._state)

    def _return_no_majority_event(self) -> Tuple[SharedState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY


class PrepareTxRound(CollectSameUntilThresholdRound, SimpleABCIAbstractRound):
    """A round in a which keeper is selected"""

    round_id = "prepare_tx"
    allowed_tx_type = TXHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_selection=MappingProxyType(self.collection),
                most_voted_keeper_address=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
                self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None


class FinishedPrepareTxRound(DegenerateRound, ABC):
    """A round that represents the transition to the RandomnessTransactionSubmissionRound"""

    round_id = "randomness_transaction_submission"


class FailedRound(DegenerateRound, ABC):
    """A round that represents that the period failed"""

    round_id = "registration"


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

    initial_round_cls: Type[AbstractRound] = PrepareTxRound
    transition_function: AbciAppTransitionFunction = {
        PrepareTxRound: {
            Event.DONE: FinishedPrepareTxRound,
            Event.RESET_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: FailedRound,
        },
        FinishedPrepareTxRound: {},
        FailedRound: {},
    }
    final_states = {
        FinishedPrepareTxRound,
        FailedRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
