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
from typing import Dict, FrozenSet, List, Optional, Set, Tuple, Type, cast

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
from packages.valory.skills.keep3r_job_abci.payloads import (
    ActivationTxPayload,
    ApproveBondTxPayload,
    BondingTxPayload,
    CalculateSpentGasPayload,
    GetJobsPayload,
    PathSelectionPayload,
    SwapAndDisburseRewardsPayload,
    TopUpPayload,
    UnbondingTxPayload,
    WaitingPayload,
    WorkTxPayload,
)


class Event(Enum):
    """Events"""

    APPROVE_BOND = "approve_bond"
    NOT_BONDED = "not_bonded"
    UNBOND = "unbond"
    BONDING_TX = "bonding_tx"
    UNBONDING_TX = "unbonding_tx"
    NOT_ACTIVATED = "not_activated"
    ACTIVATION_TX = "activation_tx"
    AWAITING_BONDING = "awaiting_bonding"
    BLACKLISTED = "blacklisted"
    WITHDRAW = "withdraw"
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
    SIMULATION_FAILED = "simulation_failed"
    ERROR = "error"


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
    def job_list(self) -> List[str]:
        """Get the job_list."""
        return cast(List[str], self.db.get_strict("job_list"))

    @property
    def workable_job(self) -> Optional[str]:
        """Get the current_job."""
        return cast(str, self.db.get_strict("workable_job"))

    @property
    def tx_submitter(self) -> str:
        """Get the round that submitted a tx to transaction_settlement_abci."""
        return cast(str, self.db.get_strict("tx_submitter"))

    @property
    def address_to_gas_spent(self) -> Dict[str, int]:
        """Get the address_to_gas_spent."""
        return cast(Dict[str, int], self.db.get_strict("address_to_gas_spent"))


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
        "UNBOND": Event.UNBOND,
        "NOT_ACTIVATED": Event.NOT_ACTIVATED,
        "HEALTHY": Event.HEALTHY,
        "INSUFFICIENT_FUNDS": Event.INSUFFICIENT_FUNDS,
        "BLACKLISTED": Event.BLACKLISTED,
        "WITHDRAW": Event.WITHDRAW,
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


class UnbondingRound(Keep3rJobAbstractRound):
    """UnbondingRound"""

    payload_class = UnbondingTxPayload
    payload_attribute: str = "unbonding_tx"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached and self.most_voted_payload:
            unbonding_tx = self.most_voted_payload
            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): unbonding_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.UNBONDING_TX
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class CalculateSpentGasRound(Keep3rJobAbstractRound):
    """CalculateSpentGasRound"""

    payload_class = CalculateSpentGasPayload
    payload_attribute: str = "address_to_gas_spent"

    ERROR_PAYLOAD = "ERROR"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            address_to_gas_spent_str = self.most_voted_payload
            if address_to_gas_spent_str == self.ERROR_PAYLOAD:
                return self.synchronized_data, Event.ERROR

            address_to_gas_spent = json.loads(address_to_gas_spent_str)
            state = self.synchronized_data.update(
                synchronized_data_class=SynchronizedData,
                **{
                    get_name(
                        SynchronizedData.address_to_gas_spent
                    ): address_to_gas_spent,
                },
            )
            return state, Event.DONE
        if not self.is_majority_possible(
            self.collection, self.synchronized_data.nb_participants
        ):
            return self.synchronized_data, Event.NO_MAJORITY
        return None


class SwapAndDisburseRewardsRound(Keep3rJobAbstractRound):
    """Round to swap and distribute the earned keeper."""

    payload_class = SwapAndDisburseRewardsPayload
    payload_attribute: str = "swap_and_disburse_tx"

    ERROR_PAYLOAD = "ERROR"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        if self.threshold_reached:
            multisend_tx = self.most_voted_payload
            if multisend_tx == self.ERROR_PAYLOAD:
                return self.synchronized_data, Event.ERROR

            state = self.synchronized_data.update(
                **{
                    get_name(SynchronizedData.most_voted_tx_hash): multisend_tx,
                    get_name(SynchronizedData.tx_submitter): self.auto_round_id(),
                }
            )
            return state, Event.DONE
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


class PerformWorkRound(Keep3rJobAbstractRound):
    """PerformWorkRound"""

    payload_class = WorkTxPayload
    payload_attribute: str = "work_tx"

    SIMULATION_FAILED_PAYLOAD = "simulation_failed"
    NO_WORKABLE_JOB_PAYLOAD = "no_job"

    def end_block(self) -> Optional[Tuple[BaseSynchronizedData, Event]]:
        """Process the end of the block."""

        _ = (Event.INSUFFICIENT_FUNDS,)
        if self.threshold_reached and self.most_voted_payload:
            work_tx = self.most_voted_payload
            if work_tx == self.SIMULATION_FAILED_PAYLOAD:
                # if the simulation failed for this job, we go back to job selection
                return self.synchronized_data, Event.SIMULATION_FAILED
            if work_tx == self.NO_WORKABLE_JOB_PAYLOAD:
                # if there is no workable job, we go back to job selection
                return self.synchronized_data, Event.NOT_WORKABLE
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
            Event.UNBOND: UnbondingRound,
            Event.BLACKLISTED: BlacklistedRound,
            Event.APPROVE_BOND: ApproveBondRound,
            Event.WITHDRAW: CalculateSpentGasRound,
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
        UnbondingRound: {
            Event.UNBONDING_TX: FinalizeBondingRound,
            Event.NO_MAJORITY: UnbondingRound,
            Event.ROUND_TIMEOUT: UnbondingRound,
        },
        CalculateSpentGasRound: {
            Event.DONE: SwapAndDisburseRewardsRound,
            Event.NO_MAJORITY: CalculateSpentGasRound,
            Event.ROUND_TIMEOUT: CalculateSpentGasRound,
            Event.ERROR: PathSelectionRound,
        },
        SwapAndDisburseRewardsRound: {
            Event.DONE: FinalizeWorkRound,
            Event.NO_MAJORITY: SwapAndDisburseRewardsRound,
            Event.ROUND_TIMEOUT: SwapAndDisburseRewardsRound,
            Event.ERROR: PathSelectionRound,
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
            Event.DONE: PerformWorkRound,
            Event.NO_MAJORITY: GetJobsRound,
            Event.ROUND_TIMEOUT: GetJobsRound,
        },
        PerformWorkRound: {
            Event.WORK_TX: FinalizeWorkRound,
            Event.INSUFFICIENT_FUNDS: PathSelectionRound,
            Event.NO_MAJORITY: PerformWorkRound,
            Event.ROUND_TIMEOUT: PerformWorkRound,
            Event.SIMULATION_FAILED: PerformWorkRound,
            Event.NOT_WORKABLE: PerformWorkRound,
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
    db_pre_conditions: Dict[AppState, Set[str]] = {PathSelectionRound: set()}
    db_post_conditions: Dict[AppState, Set[str]] = {
        FinalizeApproveBondRound: {get_name(SynchronizedData.most_voted_tx_hash)},
        FinalizeBondingRound: {get_name(SynchronizedData.most_voted_tx_hash)},
        FinalizeActivationRound: {get_name(SynchronizedData.most_voted_tx_hash)},
        FinalizeWorkRound: {get_name(SynchronizedData.most_voted_tx_hash)},
        BlacklistedRound: set(),
        DegenerateRound: set(),
    }

    cross_period_persisted_keys: FrozenSet[str] = frozenset({"safe_contract_address"})
