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
from typing import Dict, Optional, Tuple, Type, cast, Set

from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AppState,
    AbciAppTransitionFunction,
    AbstractRound,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    TransactionType,
    BaseTxPayload,
)


class Event(Enum):

    NOT_REGISTERED = "not_registered"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    ACTIVATE_TX = "activate_tx"
    BLACKLISTED = "blacklisted"
    NO_JOBS = "no_jobs"
    BOND_TX = "bond_tx"
    HEALTHY = "healthy"
    UNKNOWN_HEALTH_ISSUE = "unknown_health_issue"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"
    AWAITING_BONDING = "awaiting_bonding"
    WORKABLE = "workable"
    NOT_WORKABLE = "not_workable"
    PROFITABLE = "profitable"
    NOT_PROFITABLE = "not_profitable"
    WORK_TX = "work_tx"
    TOP_UP = "top_up"
    DONE = "done"


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


class HealthCheckRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class BondingRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class WaitRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class ActivateRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class GetJobsRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


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


class PerformWorkRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class AwaitTopUpRound(AbstractRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class BlacklistedRound(DegenerateRound):
    # TODO: replace AbstractRound with one of CollectDifferentUntilAllRound, CollectSameUntilAllRound, CollectSameUntilThresholdRound, CollectDifferentUntilThresholdRound, OnlyKeeperSendsRound, VotingRound
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class DegenerateRound(DegenerateRound):
    # TODO: set the following class attributes
    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Enum]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class Keep3rJobAbciApp(AbciApp[Event]):
    """Keep3rJobAbciApp"""

    initial_round_cls: Type[AbstractRound] = BondingRound
    initial_states: Set[AppState] = {BondingRound}
    transition_function: AbciAppTransitionFunction = {
        BondingRound: {
            Event.BOND_TX: HealthCheckRound,
            Event.NO_MAJORITY: BondingRound,
            Event.ROUND_TIMEOUT: BondingRound,
        },
        WaitRound: {
            Event.DONE: ActivateRound,
            Event.NO_MAJORITY: WaitRound,
            Event.ROUND_TIMEOUT: WaitRound,
        },
        ActivateRound: {
            Event.ACTIVATE_TX: HealthCheckRound,
            Event.AWAITING_BONDING: WaitRound,
            Event.NO_MAJORITY: ActivateRound,
            Event.ROUND_TIMEOUT: ActivateRound,
        },
        GetJobsRound: {
            Event.DONE: JobSelectionRound,
            Event.NO_MAJORITY: GetJobsRound,
            Event.ROUND_TIMEOUT: GetJobsRound,
        },
        JobSelectionRound: {
            Event.DONE: IsWorkableRound,
            Event.NO_JOBS: HealthCheckRound,
            Event.NO_MAJORITY: JobSelectionRound,
            Event.ROUND_TIMEOUT: JobSelectionRound,
        },
        IsWorkableRound: {
            Event.WORKABLE: IsProfitableRound,
            Event.NOT_WORKABLE: JobSelectionRound,
            Event.NO_MAJORITY: IsWorkableRound,
            Event.ROUND_TIMEOUT: IsWorkableRound,
        },
        IsProfitableRound: {
            Event.PROFITABLE: PerformWorkRound,
            Event.NOT_PROFITABLE: JobSelectionRound,
            Event.NO_MAJORITY: IsProfitableRound,
            Event.ROUND_TIMEOUT: IsProfitableRound,
        },
        PerformWorkRound: {
            Event.WORK_TX: HealthCheckRound,
            Event.INSUFFICIENT_FUNDS: HealthCheckRound,
            Event.NO_MAJORITY: PerformWorkRound,
            Event.ROUND_TIMEOUT: PerformWorkRound,
        },
        HealthCheckRound: {
            Event.NOT_REGISTERED: BondingRound,
            Event.HEALTHY: GetJobsRound,
            Event.INSUFFICIENT_FUNDS: AwaitTopUpRound,
            Event.BLACKLISTED: BlacklistedRound,
            Event.UNKNOWN_HEALTH_ISSUE: DegenerateRound,
        },
        AwaitTopUpRound: {
            Event.TOP_UP: HealthCheckRound,
            Event.ROUND_TIMEOUT: ActivateRound,
        },
        BlacklistedRound: {},
        DegenerateRound: {},
    }
    final_states: Set[AppState] = {DegenerateRound, BlacklistedRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys = ["safe_contract_address"]
