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
from typing import Dict, List, Optional, Set, Tuple, Type, cast

from packages.keep3r_co.skills.keep3r_job.payloads import (
    ActivationTxPayload,
    BondingTxPayload,
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    PathSelectionPayload,
    TopUpPayload,
    TransactionType,
    WaitingPayload,
    WorkTxPayload,
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
    EventToTimeout,
)


class Event(Enum):
    """Events"""

    NOT_BONDED = "not_bonded"
    BONDING_TX = "bonding_tx"
    NOT_ACTIVATED = "not_activated"
    ACTIVATION_TX = "activation_tx"
    AWAITING_BONDING = "awaiting_bonding"
    BLACKLISTED = "blacklisted"
    UNKNOWN_HEALTH_ISSUE = "unknown_health_issue"
    HEALTHY = "healthy"
    DONE = "done"
    NO_JOBS = "no_jobs"
    WORKABLE = "workable"
    NOT_WORKABLE = "not_workable"
    PROFITABLE = "profitable"
    NOT_PROFITABLE = "not_profitable"
    WORK_TX = "work_tx"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    TOP_UP = "top_up"
    NO_MAJORITY = "no_majority"
    ROUND_TIMEOUT = "round_timeout"


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
    def job_list(self) -> str:
        """Get the job_list."""
        return cast(str, self.db.get_strict("job_list"))

    @property
    def current_job(self) -> Optional[str]:
        """Get the current_job."""
        return cast(str, self.db.get_strict("current_job"))


class Keep3rJobAbstractRound(CollectSameUntilThresholdRound, ABC):
    """Keep3rJobAbstractRound"""

    synchronized_data_class = SynchronizedData

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Synchronized data"""

        return cast(SynchronizedData, super().synchronized_data)


class PathSelectionRound(Keep3rJobAbstractRound):
    """HealthCheckRound"""

    round_id: str = "path_selection"
    allowed_tx_type: TransactionType = PathSelectionPayload.transaction_type
    payload_attribute: str = "path_selection"

    transitions: Dict[str, Event] = {
        "NOT_BONDED": Event.NOT_BONDED,
        "NOT_ACTIVATED": Event.NOT_ACTIVATED,
        "HEALTHY": Event.HEALTHY,
        "INSUFFICIENT_FUNDS": Event.INSUFFICIENT_FUNDS,
        "BLACKLISTED": Event.BLACKLISTED,
        "UNKNOWN_HEALTH_ISSUE": Event.UNKNOWN_HEALTH_ISSUE,
    }

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            selected_path = self.most_voted_payload
            state = self.synchronized_data.update(selected_path=selected_path)
            return state, self.transitions[selected_path]
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class BondingRound(Keep3rJobAbstractRound):
    """BondingRound"""

    round_id: str = "bonding"
    allowed_tx_type: TransactionType = BondingTxPayload.transaction_type
    payload_attribute: str = "bonding_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached and self.most_voted_payload:
            bonding_tx = self.most_voted_payload
            state = self.synchronized_data.update(bonding_tx=bonding_tx)
            return state, Event.BONDING_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class WaitingRound(Keep3rJobAbstractRound):
    """WaitingRound"""

    round_id: str = "waiting"
    allowed_tx_type: TransactionType = WaitingPayload.transaction_type
    payload_attribute: str = "done_waiting"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            done_waiting = self.most_voted_payload
            state = self.synchronized_data.update(done_waiting=done_waiting)
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class ActivationRound(Keep3rJobAbstractRound):
    """ActivationRound"""

    round_id: str = "activation"
    allowed_tx_type: TransactionType = ActivationTxPayload.transaction_type
    payload_attribute: str = "activation_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        _ = Event.AWAITING_BONDING

        if self.threshold_reached:
            activation_tx = self.most_voted_payload
            state = self.synchronized_data.update(activation_tx=activation_tx)
            return state, Event.ACTIVATION_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class GetJobsRound(Keep3rJobAbstractRound):
    """GetJobsRound"""

    round_id: str = "get_jobs"
    allowed_tx_type: TransactionType = GetJobsPayload.transaction_type
    payload_attribute: str = str(GetJobsPayload.transaction_type)

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            job_list = self.most_voted_payload
            state = self.synchronized_data.update(job_list=job_list)
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class JobSelectionRound(Keep3rJobAbstractRound):
    """JobSelectionRound"""

    round_id = "job_selection"
    allowed_tx_type: TransactionType = JobSelectionPayload.transaction_type
    payload_attribute = "current_job"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            current_job = self.most_voted_payload
            state = self.synchronized_data.update(current_job=current_job)
            return state, Event.DONE if current_job else Event.NO_JOBS
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class IsWorkableRound(Keep3rJobAbstractRound):
    """IsWorkableRound"""

    round_id = "is_workable"
    allowed_tx_type: TransactionType = IsWorkablePayload.transaction_type
    payload_attribute = "is_workable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            is_workable = self.most_voted_payload
            if is_workable:
                state = self.synchronized_data.update(is_workable=is_workable)
                return state, Event.WORKABLE
            # remove the non-workable job and attempt another
            job_list: List[str] = self.synchronized_data.job_list.copy()
            job_list.remove(self.synchronized_data.job_selection)
            state = self.synchronized_data.update(job_list=job_list)
            return state, Event.NOT_WORKABLE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class IsProfitableRound(Keep3rJobAbstractRound):
    """IsProfitableRound"""

    round_id = "is_profitable"
    allowed_tx_type: TransactionType = IsProfitablePayload.transaction_type
    payload_attribute = "is_profitable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            state = self.synchronized_data.update(is_profitable=self.most_voted_payload)
            is_profitable = self.most_voted_payload
            if is_profitable:
                return state, Event.PROFITABLE
            return state, Event.NOT_PROFITABLE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class PerformWorkRound(Keep3rJobAbstractRound):
    """PerformWorkRound"""

    round_id: str = "perform_work"
    allowed_tx_type: TransactionType = WorkTxPayload.transaction_type
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        _ = (Event.WORK_TX, Event.INSUFFICIENT_FUNDS, Event.NO_MAJORITY)
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


class AwaitTopUpRound(Keep3rJobAbstractRound):
    """AwaitTopUpRound"""

    round_id: str = "await_top_up"
    allowed_tx_type: TransactionType = TopUpPayload.transaction_type
    payload_attribute: str

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        _ = (Event.TOP_UP, Event.NO_MAJORITY)
        raise NotImplementedError

    def check_payload(self, payload: BaseTxPayload) -> None:
        """Check payload."""
        raise NotImplementedError

    def process_payload(self, payload: BaseTxPayload) -> None:
        """Process payload."""
        raise NotImplementedError


# degenerate rounds
class FinalizeBondingRound(DegenerateRound):
    """FinalizeBondingRound"""

    round_id: str = "finalize_bonding_round"


class FinalizeActivationRound(DegenerateRound):
    """FinalizeActivationRound"""

    round_id: str = "finalize_activation_round"


class FinalizeWorkRound(DegenerateRound):
    """FinalizeWorkRound"""

    round_id: str = "finalize_work_round"


class BlacklistedRound(DegenerateRound):
    """BlacklistedRound"""

    round_id: str = "blacklisted"


class Keep3rJobAbciApp(AbciApp[Event]):
    """Keep3rJobAbciApp

    Initial round: PathSelectionRound

    Initial states: {PathSelectionRound}

    Transition states:
        0. PathSelectionRound
            - not bonded: 1.
            - not activated: 2.
            - healthy: 4.
            - insufficient funds: 9.
            - blacklisted: 13.
            - unknown health issue: 14.
            - no majority: 0.
            - round timeout: 0.
        1. BondingRound
            - bonding tx: 10.
            - no majority: 1.
            - round timeout: 1.
        2. WaitingRound
            - done: 3.
            - no majority: 2.
            - round timeout: 2.
        3. ActivationRound
            - activation tx: 11.
            - awaiting bonding: 2.
            - no majority: 3.
            - round timeout: 3.
        4. GetJobsRound
            - done: 5.
            - no majority: 4.
            - round timeout: 4.
        5. JobSelectionRound
            - done: 6.
            - no jobs: 0.
            - no majority: 5.
            - round timeout: 5.
        6. IsWorkableRound
            - workable: 7.
            - not workable: 5.
            - no majority: 6.
            - round timeout: 6.
        7. IsProfitableRound
            - profitable: 8.
            - not profitable: 5.
            - no majority: 7.
            - round timeout: 7.
        8. PerformWorkRound
            - work tx: 12.
            - insufficient funds: 0.
            - no majority: 8.
            - round timeout: 8.
        9. AwaitTopUpRound
            - top up: 0.
            - no majority: 9.
            - round timeout: 9.
        10. FinalizeBondingRound
        11. FinalizeActivationRound
        12. FinalizeWorkRound
        13. BlacklistedRound
        14. DegenerateRound

    Final states: {FinalizeBondingRound, FinalizeActivationRound, FinalizeWorkRound, BlacklistedRound, DegenerateRound}

    Timeouts:
        round timeout: 30.0
    """

    initial_round_cls: Type[AbstractRound] = PathSelectionRound

    initial_states: Set[AppState] = {PathSelectionRound}

    transition_function: AbciAppTransitionFunction = {
        PathSelectionRound: {
            Event.NOT_BONDED: BondingRound,
            Event.NOT_ACTIVATED: WaitingRound,
            Event.HEALTHY: GetJobsRound,
            Event.INSUFFICIENT_FUNDS: AwaitTopUpRound,
            Event.BLACKLISTED: BlacklistedRound,
            Event.UNKNOWN_HEALTH_ISSUE: DegenerateRound,
            Event.NO_MAJORITY: PathSelectionRound,
            Event.ROUND_TIMEOUT: PathSelectionRound,
        },
        BondingRound: {
            Event.BONDING_TX: FinalizeBondingRound,
            Event.NO_MAJORITY: BondingRound,
            Event.ROUND_TIMEOUT: BondingRound,
        },
        WaitingRound: {
            Event.DONE: ActivationRound,
            Event.NO_MAJORITY: WaitingRound,
            Event.ROUND_TIMEOUT: WaitingRound,
        },
        ActivationRound: {
            Event.ACTIVATION_TX: FinalizeActivationRound,
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
            Event.NO_JOBS: PathSelectionRound,
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
            Event.WORK_TX: FinalizeWorkRound,
            Event.INSUFFICIENT_FUNDS: PathSelectionRound,
            Event.NO_MAJORITY: PerformWorkRound,
            Event.ROUND_TIMEOUT: PerformWorkRound,
        },
        AwaitTopUpRound: {
            Event.TOP_UP: PathSelectionRound,
            Event.NO_MAJORITY: AwaitTopUpRound,
            Event.ROUND_TIMEOUT: AwaitTopUpRound,
        },
        FinalizeBondingRound: {},
        FinalizeActivationRound: {},
        FinalizeWorkRound: {},
        BlacklistedRound: {},
        DegenerateRound: {},
    }

    final_states: Set[AppState] = {
        FinalizeBondingRound,
        FinalizeActivationRound,
        FinalizeWorkRound,
        BlacklistedRound,
        DegenerateRound,
    }

    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }

    cross_period_persisted_keys: List[str] = ["safe_contract_address"]
