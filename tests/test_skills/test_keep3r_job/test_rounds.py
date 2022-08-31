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

"""Test the base.py module of the skill."""
import logging  # noqa: F401
from types import MappingProxyType
from typing import Any, FrozenSet, Type, cast
from unittest import mock

import pytest

from packages.keep3r_co.skills.keep3r_job.payloads import (
    BaseKeep3rJobPayload,
    BondingTxPayload,
    GetJobsPayload,
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    PathSelectionPayload,
    WorkTxPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
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

    def setup(self) -> None:
        """Setup the test method."""

        self.participants = get_participants()
        data = dict(participants=self.participants, all_participants=self.participants)
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

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            state, event = result
            assert event == Event.NO_MAJORITY


class TestPathSelectionRound(BaseRoundTestClass):
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
    """Tests for PathSelectionRound."""

    round_class = BondingRound
    payload_class = BondingTxPayload

    @pytest.mark.parametrize("bonding_tx", ["some_raw_tx_hash"])
    def test_run(self, bonding_tx: str) -> None:
        """Run tests."""

        next_state = self.deliver_payloads(bonding_tx=bonding_tx)
        event = self.complete_round(next_state)
        assert event == Event.BONDING_TX


class TestGetJobsRound(BaseRoundTestClass):
    """Tests for GetJobsRound."""

    round_class = GetJobsRound
    payload_class = GetJobsPayload

    def test_run(self) -> None:
        """Run tests."""

        job_list = ["some_job_address"]
        next_state = self.deliver_payloads(job_list=job_list)
        event = self.complete_round(next_state)
        assert event == Event.DONE


@pytest.mark.skip("ABCIApp redesign: no payment assigned yet")
class TestPerformWorkRound(BaseRoundTestClass):
    """Tests for PrepareTxRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = PerformWorkRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        test_hash = "test_hash"

        first_payload, *payloads = [
            WorkTxPayload(sender=participant, work_tx=test_hash)
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection == {first_payload.sender: first_payload}
        assert test_round.end_block() is None

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            most_voted_tx_hash=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(SynchronizedData, state).participants
            == cast(SynchronizedData, actual_next_state).participants
        )
        assert event == Event.DONE


class TestJobSelectionRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    round_class = JobSelectionRound

    def test_selects_job(
        self,
    ) -> None:
        """Run tests."""

        test_round = JobSelectionRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            JobSelectionPayload(
                sender=participant,
                job_selection="some_job",
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            job_selection=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(SynchronizedData, state).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_state
                ).participant_to_selection
            ]
        )
        assert event == Event.DONE


class TestIsWorkableRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    round_class = IsWorkableRound

    def test_run_positive(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsWorkableRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            IsWorkablePayload(
                sender=participant,
                is_workable=True,
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_workable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(SynchronizedData, state).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_state
                ).participant_to_selection
            ]
        )
        assert event == Event.WORKABLE

    def test_run_negative(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsWorkableRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            IsWorkablePayload(
                sender=participant,
                is_workable=False,
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_workable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(SynchronizedData, state).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_state
                ).participant_to_selection
            ]
        )
        assert event == Event.NOT_WORKABLE


class TestIsProfitableRound(BaseRoundTestClass):
    """Tests for ProfitabilityRound."""

    round_class = IsProfitableRound

    def test_run_positive(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsProfitableRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            IsProfitablePayload(
                sender=participant,
                is_profitable=True,
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_profitable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(SynchronizedData, state).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_state
                ).participant_to_selection
            ]
        )
        assert event == Event.PROFITABLE

    def test_run_negative(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsProfitableRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            IsProfitablePayload(
                sender=participant,
                is_profitable=False,
            )
            for participant in self.participants
        ]

        test_round.process_payload(first_payload)
        assert test_round.collection[first_payload.sender] == first_payload
        assert test_round.end_block() is None

        self._test_no_majority_event(test_round)

        for payload in payloads:
            test_round.process_payload(payload)

        actual_next_state = self.synchronized_data.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_profitable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(SynchronizedData, state).participant_to_selection
                for key in cast(
                    SynchronizedData, actual_next_state
                ).participant_to_selection
            ]
        )
        assert event == Event.NOT_PROFITABLE
