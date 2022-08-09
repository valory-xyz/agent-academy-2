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
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    SafeExistencePayload,
    TXHashPayload,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
)


class Event(Enum):
    """Event enumeration for the simple abci demo."""

    NEGATIVE = "negative"
    DONE = "done"
    NOT_WORKABLE = "not_workable"
    ROUND_TIMEOUT = "round_timeout"
    NO_MAJORITY = "no_majority"
    NOT_PROFITABLE = "not_profitable"


class SynchronizedData(
    BaseSynchronizedData
):  # pylint: disable=too-many-instance-attributes
    """
    Class to represent synchronization data.

    This state is replicated by the tendermint application.
    """

    @property
    def safe_contract_address(self) -> str:
        """Get the safe contract address."""
        return cast(str, self.db.get_strict("safe_contract_address"))

    @property
    def most_voted_tx_hash(self) -> str:
        """Get the most_voted_tx_hash."""
        return cast(str, self.db.get_strict("most_voted_tx_hash"))

    @property
    def job_selection(self) -> str:
        """Get the job_selection."""
        return cast(str, self.db.get_strict("job_selection"))


class Keep3rJobAbstractRound(CollectSameUntilThresholdRound, ABC):
    """Abstract round for the simple abci skill."""

    synchronized_data_class = SynchronizedData


class IsWorkableRound(Keep3rJobAbstractRound):
    """Check whether the keep3r job contract is workable."""

    round_id = "is_workable"
    allowed_tx_type = IsWorkablePayload.transaction_type
    payload_attribute = "is_workable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                is_workable=self.most_voted_payload,
            )
            is_workable = self.most_voted_payload
            if is_workable:
                return state, Event.DONE
            return state, Event.NOT_WORKABLE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class JobSelectionRound(Keep3rJobAbstractRound):
    """Handle the keep3r job selection."""

    round_id = "job_selection"
    allowed_tx_type = JobSelectionPayload.transaction_type
    payload_attribute = "job_selection"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            job_selection = self.most_voted_payload
            state = self.synchronized_data.update(job_selection=job_selection)
            if job_selection:
                return state, Event.DONE
            return state, Event.NOT_WORKABLE  # NO_JOBS ?
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class PrepareTxRound(Keep3rJobAbstractRound):
    """A round in a which transaction hash is prepared"""

    round_id = "prepare_tx"
    allowed_tx_type = TXHashPayload.transaction_type
    payload_attribute = "tx_hash"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                most_voted_tx_hash=self.most_voted_payload,
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class IsProfitableRound(Keep3rJobAbstractRound):
    """The round in which profitability of a job is estimated"""

    round_id = "get_is_profitable"
    allowed_tx_type = IsProfitablePayload.transaction_type
    payload_attribute = "is_profitable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(is_profitable=self.most_voted_payload)
            is_profitable = self.most_voted_payload
            if is_profitable:
                return state, Event.DONE
            return state, Event.NOT_PROFITABLE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class FinishedPrepareTxRound(DegenerateRound, ABC):
    """A round that represents transaction hash preparation has finalized"""

    round_id = "finished_prepare_tx_round"


class FailedRound(DegenerateRound, ABC):
    """A round that represents failure of the round sequence"""

    round_id = "failed_round"


class NothingToDoRound(DegenerateRound, ABC):
    """A round that represents that there is no worthwhile work"""

    round_id = "nothing_to_do"


class CheckSafeExistenceRound(Keep3rJobAbstractRound):
    """A round in a which existence of the safe address is validated"""

    round_id = "check_safe_existence"
    allowed_tx_type = SafeExistencePayload.transaction_type
    payload_attribute = "safe_exists"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            state = self.synchronized_data.update(
                safe_exists=self.most_voted_payload,
            )
            safe_exists = self.most_voted_payload
            if safe_exists:
                return state, Event.DONE
            return state, Event.NEGATIVE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class SafeNotDeployedRound(DegenerateRound, ABC):
    """A round that represents that the safe is not deployed"""

    round_id = "safe_not_deployed_round"


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

    initial_round_cls: Type[AbstractRound] = CheckSafeExistenceRound
    transition_function: AbciAppTransitionFunction = {
        CheckSafeExistenceRound: {
            Event.DONE: JobSelectionRound,  # To the last round of safe deployment abci
            Event.NEGATIVE: SafeNotDeployedRound,  # To the 1st round of safe deployment abci
            Event.ROUND_TIMEOUT: CheckSafeExistenceRound,
            Event.NO_MAJORITY: CheckSafeExistenceRound,
        },
        JobSelectionRound: {
            Event.DONE: IsWorkableRound,
            Event.NOT_WORKABLE: NothingToDoRound,
            Event.ROUND_TIMEOUT: JobSelectionRound,
            Event.NO_MAJORITY: JobSelectionRound,
        },
        IsWorkableRound: {
            Event.DONE: IsProfitableRound,
            Event.NOT_WORKABLE: NothingToDoRound,
            Event.ROUND_TIMEOUT: IsWorkableRound,
            Event.NO_MAJORITY: IsWorkableRound,
        },
        IsProfitableRound: {
            Event.DONE: PrepareTxRound,
            Event.NOT_PROFITABLE: NothingToDoRound,
            Event.NO_MAJORITY: IsProfitableRound,
            Event.ROUND_TIMEOUT: IsProfitableRound,
        },
        PrepareTxRound: {
            Event.DONE: FinishedPrepareTxRound,
            Event.ROUND_TIMEOUT: FailedRound,
            Event.NO_MAJORITY: PrepareTxRound,
        },
        SafeNotDeployedRound: {},
        FinishedPrepareTxRound: {},
        FailedRound: {},
        NothingToDoRound: {},
    }
    final_states = {
        FinishedPrepareTxRound,
        FailedRound,
        NothingToDoRound,
        SafeNotDeployedRound,
    }
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys = ["safe_contract_address"]
