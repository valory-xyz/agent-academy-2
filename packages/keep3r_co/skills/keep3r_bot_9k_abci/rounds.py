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

"""This module contains the data classes for the Keep3r Bot ABCI application."""
from abc import ABC
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple, Type, cast

from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BasePeriodState,
    CollectSameUntilThresholdRound,
)
from packages.keep3r_co.skills.keep3r_bot_9k_abci.payloads import (
    IsWorkablePayload,
    TransactionType,
)


class Event(Enum):
    """Event enumeration for the Keep3r Bot abci."""

    DONE = "done"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    RESET_TIMEOUT = "reset_timeout"


class PeriodState(BasePeriodState):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent a period state.

    This state is replicated by the tendermint application.
    """

    @property
    def participant_to_is_workable(self) -> Mapping[str, IsWorkablePayload]:
        """Get the participant_to_is_workable."""
        return cast(
            Mapping[str, IsWorkablePayload],
            self.db.get_strict("participant_to_is_workable"),
        )

    @property
    def most_voted_is_workable(self) -> str:
        """Get the most_voted_is_workable."""
        return cast(str, self.db.get_strict("most_voted_is_workable"))


class Keep3rBotABCIAbstractRound(AbstractRound[Event, TransactionType], ABC):
    """Abstract round for the keep3r bot abci skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, self._state)

    def _return_no_majority_event(self) -> Tuple[PeriodState, Event]:
        """
        Trigger the NO_MAJORITY event.

        :return: a new period state and a NO_MAJORITY event
        """
        return self.period_state, Event.NO_MAJORITY



class IsWorkableRound(CollectSameUntilThresholdRound, Keep3rBotABCIAbstractRound):
    """Check whether the keep3r job contract is workable."""

    round_id = "is_workable"
    allowed_tx_type = IsWorkablePayload.transaction_type
    payload_attribute = "is_workable"

    def end_block(self) -> Optional[Tuple[BasePeriodState, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.period_state.update(
                participant_to_is_workable=MappingProxyType(self.collection),
                most_voted_is_workable=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.period_state.nb_participants
        ):
            return self._return_no_majority_event()
        return None




class Keep3rBotAbciApp(AbciApp[Event]):
    """Keep3rBotAbciApp

    Initial round:

    Initial states:

    Transition states:


    Final states: {}

    Timeouts:
        round timeout: 30.0
        reset timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound]
    transition_function: AbciAppTransitionFunction
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
        Event.RESET_TIMEOUT: 30.0,
    }
