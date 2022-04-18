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

from packages.keep3r_co.skills.keep3r_job.payloads import (
    IsWorkablePayload,
    TXHashPayload,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    Event,
    IsWorkableRound,
    PeriodState,
    PrepareTxRound,
)
from packages.valory.skills.abstract_round_abci.base import (
    AbstractRound,
    ConsensusParams,
    StateDB,
)


MAX_PARTICIPANTS: int = 4


def get_participants() -> FrozenSet[str]:
    """Participants"""
    return frozenset([f"agent_{i}" for i in range(MAX_PARTICIPANTS)])


class BaseRoundTestClass:
    """Base test class for Rounds."""

    period_state: PeriodState
    consensus_params: ConsensusParams
    participants: FrozenSet[str]

    @classmethod
    def setup(
        cls,
    ) -> None:
        """Setup the test class."""

        cls.participants = get_participants()
        cls.period_state = PeriodState(
            StateDB(
                initial_period=0,
                initial_data=dict(
                    participants=cls.participants, all_participants=cls.participants
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
            state=self.period_state, consensus_params=self.consensus_params
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

        actual_next_state = self.period_state.update(
            most_voted_tx_hash=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert (
            cast(PeriodState, state).participants
            == cast(PeriodState, actual_next_state).participants
        )
        assert event == Event.DONE


class TestIsWorkableRound(BaseRoundTestClass):
    """Tests for RegistrationRound."""

    def test_run_positive(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsWorkableRound(
            state=self.period_state, consensus_params=self.consensus_params
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

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_workable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(PeriodState, state).participant_to_selection
                for key in cast(PeriodState, actual_next_state).participant_to_selection
            ]
        )
        assert event == Event.DONE

    def test_run_negative(
        self,
    ) -> None:
        """Run tests."""

        test_round = IsWorkableRound(
            state=self.period_state, consensus_params=self.consensus_params
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

        actual_next_state = self.period_state.update(
            participant_to_selection=MappingProxyType(test_round.collection),
            is_workable=test_round.most_voted_payload,
        )

        res = test_round.end_block()
        assert res is not None
        state, event = res
        assert all(
            [
                key in cast(PeriodState, state).participant_to_selection
                for key in cast(PeriodState, actual_next_state).participant_to_selection
            ]
        )
        assert event == Event.NOT_WORKABLE
