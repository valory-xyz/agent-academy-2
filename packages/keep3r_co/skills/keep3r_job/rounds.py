# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
import json
from abc import ABC
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Type, cast

from packages.keep3r_co.skills.keep3r_job.payloads import (
    ActivationTxPayload,
    ApproveBondTxPayload,
    BondingTxPayload,
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    PathSelectionPayload,
    TopUpPayload,
    WaitingPayload,
    WorkTxPayload,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciApp,
    AbciAppTransitionFunction,
    AbstractRound,
    AppState,
    BaseSynchronizedData,
    CollectSameUntilThresholdRound,
    DegenerateRound,
    EventToTimeout,
    get_name,
)


class Event(Enum):
    """Events"""

    APPROVE_BOND = "approve_bond"
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

    @property
    def tx_submitter(self) -> str:
        """Get the round that submitted a tx to transaction_settlement_abci."""
        return cast(str, self.db.get_strict("tx_submitter"))


class Keep3rJobAbstractRound(CollectSameUntilThresholdRound, ABC):
    """Keep3rJobAbstractRound"""

    synchronized_data_class = SynchronizedData

    @property
    def synchronized_data(self) -> SynchronizedData:
        """Synchronized data"""

        return cast(SynchronizedData, super().synchronized_data)


class PathSelectionRound(Keep3rJobAbstractRound):
    """HealthCheckRound"""

    payload_class = PathSelectionPayload
    payload_attribute: str = "path_selection"

    transitions: Dict[str, Event] = {
        "APPROVE_BOND": Event.APPROVE_BOND,
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


class ApproveBondRound(Keep3rJobAbstractRound):
    """Round to approve the keep3r contract to spend our (erc20) tokens."""

    payload_class = ApproveBondTxPayload
    payload_attribute: str = "approval_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            approval_tx = self.most_voted_payload
            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): approval_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.APPROVE_BOND
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class BondingRound(Keep3rJobAbstractRound):
    """BondingRound"""

    payload_class = BondingTxPayload
    payload_attribute: str = "bonding_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached and self.most_voted_payload:
            bonding_tx = self.most_voted_payload
            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): bonding_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.BONDING_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class WaitingRound(Keep3rJobAbstractRound):
    """WaitingRound"""

    payload_class = WaitingPayload
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

    payload_class = ActivationTxPayload
    payload_attribute: str = "activation_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        _ = Event.AWAITING_BONDING

        if self.threshold_reached:
            activation_tx = self.most_voted_payload
            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): activation_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.ACTIVATION_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class GetJobsRound(Keep3rJobAbstractRound):
    """GetJobsRound"""

    payload_class = GetJobsPayload
    payload_attribute: str = "job_list"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            job_list_str = self.most_voted_payload
            job_list = json.loads(job_list_str)
            state = self.synchronized_data.update(job_list=job_list)
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class JobSelectionRound(Keep3rJobAbstractRound):
    """JobSelectionRound"""

    payload_class = JobSelectionPayload
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

    payload_class = IsWorkablePayload
    payload_attribute = "is_workable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""
        if self.threshold_reached:
            is_workable = self.most_voted_payload
            if is_workable:
                state = self.synchronized_data.update(is_workable=is_workable)
                return state, Event.WORKABLE
            # remove the non-workable job, then transition to JobSelectionRound
            current_job = cast(str, self.synchronized_data.current_job)
            job_list = self.synchronized_data.job_list.replace(current_job, "")
            state = self.synchronized_data.update(job_list=job_list)
            return state, Event.NOT_WORKABLE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class IsProfitableRound(Keep3rJobAbstractRound):
    """IsProfitableRound"""

    payload_class = IsProfitablePayload
    payload_attribute = "is_profitable"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            is_profitable = self.most_voted_payload
            state = self.synchronized_data.update(is_profitable=is_profitable)
            return state, Event.PROFITABLE if is_profitable else Event.NOT_PROFITABLE

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class PerformWorkRound(Keep3rJobAbstractRound):
    """PerformWorkRound"""

    payload_class = WorkTxPayload
    payload_attribute: str = "work_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        _ = (Event.INSUFFICIENT_FUNDS,)
        if self.threshold_reached and self.most_voted_payload:
            work_tx = self.most_voted_payload
            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): work_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.WORK_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class AwaitTopUpRound(Keep3rJobAbstractRound):
    """AwaitTopUpRound"""

    payload_class = TopUpPayload
    payload_attribute: str = "top_up"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached and self.most_voted_payload:
            top_up = self.most_voted_payload
            state = self.synchronized_data.update(top_up=top_up)
            return state, Event.TOP_UP

        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


# degenerate rounds
class FinalizeApproveBondRound(DegenerateRound):
    """FinalizeBondingRound"""


class FinalizeBondingRound(DegenerateRound):
    """FinalizeBondingRound"""


class FinalizeActivationRound(DegenerateRound):
    """FinalizeActivationRound"""


class FinalizeWorkRound(DegenerateRound):
    """FinalizeWorkRound"""


class BlacklistedRound(DegenerateRound):
    """BlacklistedRound"""


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
            Event.APPROVE_BOND: ApproveBondRound,
            Event.UNKNOWN_HEALTH_ISSUE: DegenerateRound,
            Event.NO_MAJORITY: PathSelectionRound,
            Event.ROUND_TIMEOUT: PathSelectionRound,
        },
        ApproveBondRound: {
            Event.APPROVE_BOND: FinalizeApproveBondRound,
            Event.NO_MAJORITY: ApproveBondRound,
            Event.ROUND_TIMEOUT: ApproveBondRound,
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
        FinalizeApproveBondRound: {},
        FinalizeBondingRound: {},
        FinalizeActivationRound: {},
        FinalizeWorkRound: {},
        BlacklistedRound: {},
        DegenerateRound: {},
    }

    final_states: Set[AppState] = {
        FinalizeApproveBondRound,
        FinalizeBondingRound,
        FinalizeActivationRound,
        FinalizeWorkRound,
        BlacklistedRound,
        DegenerateRound,
    }

    event_to_timeout: EventToTimeout = {
        Event.ROUND_TIMEOUT: 30.0,
    }
    db_pre_conditions: Dict[AppState, List[str]] = {PathSelectionRound: []}
    db_post_conditions: Dict[AppState, List[str]] = {
        FinalizeApproveBondRound: [get_name(SynchronizedData.most_voted_tx_hash)],
        FinalizeBondingRound: [get_name(SynchronizedData.most_voted_tx_hash)],
        FinalizeActivationRound: [get_name(SynchronizedData.most_voted_tx_hash)],
        FinalizeWorkRound: [get_name(SynchronizedData.most_voted_tx_hash)],
        BlacklistedRound: [],
        DegenerateRound: [],
    }

    cross_period_persisted_keys: List[str] = ["safe_contract_address"]
