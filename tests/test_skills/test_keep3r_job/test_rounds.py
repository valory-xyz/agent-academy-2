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
from typing import FrozenSet, cast
from unittest import mock

from packages.valory.skills.abstract_round_abci.base import (
    AbciAppDB,
    AbstractRound,
    ConsensusParams,
)
from packages.valory.skills.keep3r_job.payloads import (
    IsProfitablePayload,
    IsWorkablePayload,
    JobSelectionPayload,
    SafeExistencePayload,
    TXHashPayload,
)
from packages.valory.skills.keep3r_job.rounds import (
    CheckSafeExistenceRound,
    Event,
    IsProfitableRound,
    IsWorkableRound,
    JobSelectionRound,
    PrepareTxRound,
    SynchronizedData,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class BaseRoundTestClass:
    """Base test class for Rounds."""

    synchronized_data: SynchronizedData
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(cls) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.synchronized_data = SynchronizedData(
            AbciAppDB(
                setup_data=dict(
                    participants=[cls.participants],
                    all_participants=[cls.participants],
                ),
            )
        )
        cls.consensus_params = ConsensusParams(max_participants=MAX_PARTICIPANTS)

    def _test_no_majority_event(self, round_obj: AbstractRound) -> None:
        """Test the NO_MAJORITY event."""
        with mock.patch.object(round_obj, "is_majority_possible", return_value=False):
            result = round_obj.end_block()
            assert result is not None
            state, event = result
            assert event == Event.NO_MAJORITY


class TestPrepareTxRound(BaseRoundTestClass):
    """Tests for PrepareTxRound."""

    def test_run(
        self,
    ) -> None:
        """Run tests."""

        test_round = PrepareTxRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )
        test_hash = "test_hash"

        first_payload, *payloads = [
            TXHashPayload(sender=participant, tx_hash=test_hash)
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


class TestSafeExistenceRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    def test_run_negative(
        self,
    ) -> None:
        """Run tests."""

        test_round = CheckSafeExistenceRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            SafeExistencePayload(
                sender=participant,
                safe_exists=False,
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
            safe_exists=test_round.most_voted_payload,
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
        assert event == Event.NEGATIVE

    def test_run_positive(
        self,
    ) -> None:
        """Run tests."""
        test_round = CheckSafeExistenceRound(
            synchronized_data=self.synchronized_data,
            consensus_params=self.consensus_params,
        )

        first_payload, *payloads = [
            SafeExistencePayload(
                sender=participant,
                safe_exists=True,
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
            safe_exists=test_round.most_voted_payload,
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


class TestJobSelectionRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

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
        assert event == Event.DONE

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
        assert event == Event.DONE

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
