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

"""Test the base.py module of the skill."""
import json
from typing import Any, FrozenSet, Optional, Type, cast
from unittest import mock

import pytest

from packages.keep3r_co.skills.keep3r_job.payloads import (
    ActivationTxPayload,
    BaseKeep3rJobPayload,
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
from packages.keep3r_co.skills.keep3r_job.rounds import (
    ActivationRound,
    AwaitTopUpRound,
    BondingRound,
    Event,
    GetJobsRound,
    IsProfitableRound,
    IsWorkableRound,
    JobSelectionRound,
    Keep3rJobAbstractRound,
    PathSelectionRound,
    PerformWorkRound,
    SynchronizedData,
    WaitingRound,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    AbstractRound,
    ConsensusParams,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset(f"agent_{i}" for i in range(MAX_PARTICIPANTS))


class BaseRoundTestClass:
    """Base test class for Rounds."""

    round_class: Type[Keep3rJobAbstractRound]
    payload_class: Type[BaseKeep3rJobPayload]
    round: Keep3rJobAbstractRound
    payload: BaseKeep3rJobPayload
    synchronized_data: SynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    def setup(self, **kwargs: Any) -> None:
        """Setup the test method."""

        self.participants = get_participants()
        data = dict(participants=self.participants, all_participants=self.participants)
        data.update(kwargs)
        self.synchronized_data = SynchronizedData(
            AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))
        )
        self.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)
        self.round = self.round_class(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

    def deliver_payloads(self, **content: Any) -> SynchronizedData:
        """Deliver payloads"""

        payloads = [self.payload_class(sender=p, **content) for p in self.participants]
        first_payload, *payloads = payloads
        self.round.process_payload(first_payload)
        assert self.round.collection == {first_payload.sender: first_payload}
        assert self.round.end_block() is None
        self._test_no_majority_event(self.round)
        for payload in payloads:
            self.round.process_payload(payload)

        kwargs = dict(path_selection=self.round.most_voted_payload)
        return cast(SynchronizedData, self.synchronized_data.update(**kwargs))

    def complete_round(self, expected_state: SynchronizedData) -> Event:
        """Complete round"""

        res = self.round.end_block()
        assert res is not None
        state, event = res
        assert state.db == expected_state.db
        return cast(Event, event)

    def _test_no_majority_event(  # pylint: disable=no-self-use
        self, round_obj: AbstractRound
    ) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            _, event = result
            assert event == Event.NO_MAJORITY


class TestPathSelectionRound(
    BaseRoundTestClass
):  # pylint: disable=too-few-public-methods
    """Tests for PathSelectionRound."""

    round_class = PathSelectionRound
    payload_class = PathSelectionPayload

    @pytest.mark.parametrize("path_selection", PathSelectionRound.transitions)
    def test_run(self, path_selection: str) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(path_selection=path_selection)
        event = self.complete_round(next_state)
        assert event == PathSelectionRound.transitions[path_selection]


class TestBondingRound(BaseRoundTestClass):
    """Tests for BondingRound."""

    round_class = BondingRound
    payload_class = BondingTxPayload

    @pytest.mark.parametrize("bonding_tx", ["some_raw_tx_hash"])
    def test_run(self, bonding_tx: str) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(bonding_tx=bonding_tx)
        event = self.complete_round(next_state)
        assert event == Event.BONDING_TX


class TestWaitingRound(BaseRoundTestClass):
    """Tests for BondingRound."""

    round_class = WaitingRound
    payload_class = WaitingPayload

    @pytest.mark.parametrize("done_waiting", [True])
    def test_run(self, done_waiting: bool) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(done_waiting=done_waiting)
        event = self.complete_round(next_state)
        assert event == Event.DONE


class TestActivationRound(BaseRoundTestClass):
    """Tests for ActivationRound."""

    round_class = ActivationRound
    payload_class = ActivationTxPayload

    @pytest.mark.parametrize("activation_tx", ["some_raw_tx_hash"])
    def test_run(self, activation_tx: str) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(activation_tx=activation_tx)
        event = self.complete_round(next_state)
        assert event == Event.ACTIVATION_TX


class TestGetJobsRound(BaseRoundTestClass):
    """Tests for GetJobsRound."""

    round_class = GetJobsRound
    payload_class = GetJobsPayload

    def test_run(self) -> None:
        """Run tests."""

        job_list = json.dumps(["some_job_address"])
        next_state = self.deliver_payloads(job_list=job_list)
        event = self.complete_round(next_state)
        assert event == Event.DONE


class TestJobSelectionRound(BaseRoundTestClass):
    """Tests for JobSelectionRound."""

    round_class = JobSelectionRound
    payload_class = JobSelectionPayload

    @pytest.mark.parametrize("current_job", [None, "some_job_address"])
    def test_selects_job(self, current_job: Optional[str]) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(current_job=current_job)
        event = self.complete_round(next_state)
        assert event == Event.DONE if current_job else Event.NO_JOBS


class TestIsWorkableRound(BaseRoundTestClass):
    """Tests for IsWorkableRound."""

    round_class = IsWorkableRound
    payload_class = IsWorkablePayload

    def setup(self, **kwargs: Any) -> None:
        """Setup"""

        job_list = "some_job_address"
        kwargs.update(job_list=job_list, current_job=job_list)
        super().setup(**kwargs)

    @pytest.mark.parametrize("is_workable", [True, False])
    def test_run(self, is_workable: bool) -> None:
        """Run tests"""

        next_state = self.deliver_payloads(is_workable=is_workable)
        event = self.complete_round(next_state)
        assert event == Event.WORKABLE if is_workable else Event.NOT_WORKABLE


class TestIsProfitableRound(BaseRoundTestClass):
    """Tests for ProfitabilityRound."""

    round_class = IsProfitableRound
    payload_class = IsProfitablePayload

    @pytest.mark.parametrize("is_profitable", [True, False])
    def test_run(self, is_profitable: bool) -> None:
        """Run tests"""

        next_state = self.deliver_payloads(is_profitable=is_profitable)
        event = self.complete_round(next_state)
        assert event == Event.PROFITABLE if is_profitable else Event.NOT_PROFITABLE


class TestPerformWorkRound(BaseRoundTestClass):
    """Tests for PrepareTxRound."""

    round_class = PerformWorkRound
    payload_class = WorkTxPayload

    @pytest.mark.parametrize("work_tx", ["some_raw_tx_hash"])
    def test_run(self, work_tx: str) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(work_tx=work_tx)
        event = self.complete_round(next_state)
        assert event == Event.WORK_TX


class TestAwaitTopUpRound(BaseRoundTestClass):
    """Tests for AwaitTopUpRound."""

    round_class = AwaitTopUpRound
    payload_class = TopUpPayload

    @pytest.mark.parametrize("top_up", [True])
    def test_run(self, top_up: bool) -> None:
        """Run tests"""

        next_state = self.deliver_payloads(top_up=top_up)
        event = self.complete_round(next_state)
        assert event == Event.TOP_UP
