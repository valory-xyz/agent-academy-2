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
from typing import Dict, Optional, Set, Tuple, Type, cast

from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    BaseTxPayload,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    TransactionType,
)


class Event(Enum):
    """Events"""

    ACTIVATION_TX = "activation_tx"
    NOT_REGISTERED = "not_registered"
    NO_JOBS = "no_jobs"
    DONE = "done"
    NOT_WORKABLE = "not_workable"
    AWAITING_BONDING = "awaiting_bonding"
    BONDING_TX = "bonding_tx"
    TOP_UP = "top_up"
    WORKABLE = "workable"
    HEALTHY = "healthy"
    WORK_TX = "work_tx"
    UNKNOWN_HEALTH_ISSUE = "unknown_health_issue"
    BLACKLISTED = "blacklisted"
    ROUND_TIMEOUT = "round_timeout"
    NOT_PROFITABLE = "not_profitable"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    PROFITABLE = "profitable"
    NO_MAJORITY = "no_majority"


class SynchronizedData(BaseSynchronizedData):
    """SynchronizedData"""

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
    """Keep3rJobAbstractRound"""

    synchronized_data_class = SynchronizedData


class HealthCheckRound(Keep3rJobAbstractRound):
    """HealthCheckRound"""

    round_id: str = "health_check"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class BondingRound(Keep3rJobAbstractRound):
    """BondingRound"""

    round_id: str = "bonding"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class WaitingRound(Keep3rJobAbstractRound):
    """WaitingRound"""

    round_id: str = "waiting"
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class ActivationRound(Keep3rJobAbstractRound):
    """ActivationRound"""

    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class GetJobsRound(AbstractRound):
    """GetJobsRound"""

    round_id: str
    allowed_tx_type: Optional[TransactionType]
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class JobSelectionRound(Keep3rJobAbstractRound):
    """JobSelectionRound"""

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
    """IsWorkableRound"""

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
    """IsProfitableRound"""

    round_id = "is_profitable"
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
    """PerformWorkRound"""

    round_id: str = "perform_work"
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
    """AwaitTopUpRound"""

    round_id: str = "await_top_up"
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
    """BlacklistedRound"""

    round_id: str = "blacklisted"
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
    """DegenerateRound"""

    round_id: str = "degenerate"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
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
            Event.BONDING_TX: HealthCheckRound,
            Event.NO_MAJORITY: BondingRound,
            Event.ROUND_TIMEOUT: BondingRound,
        },
        WaitingRound: {
            Event.DONE: ActivationRound,
            Event.NO_MAJORITY: WaitingRound,
            Event.ROUND_TIMEOUT: WaitingRound,
        },
        ActivationRound: {
            Event.ACTIVATION_TX: HealthCheckRound,
            Event.AWAITING_BONDING: WaitingRound,
            Event.NO_MAJORITY: ActivationRound,
            Event.ROUND_TIMEOUT: ActivationRound,
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
            Event.ROUND_TIMEOUT: AwaitTopUpRound,
        },
        BlacklistedRound: {},
        DegenerateRound: {},
    }
    final_states: Set[AppState] = {DegenerateRound, BlacklistedRound}
    event_to_timeout: Dict[Event, float] = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    cross_period_persisted_keys = ["safe_contract_address"]
