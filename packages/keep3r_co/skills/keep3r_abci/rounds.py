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

"""This module contains the data classes for the preliminary check of safe contract existence in the keep3r ABCI application."""
from enum import Enum

from packages.keep3r_co.skills.keep3r_abci.payloads import SafeExistencePayload
from packages.valory.skills.abstract_round_abci.base import (
    VotingRound,
)


class Event(Enum):
    """Event enumeration for the price estimation demo."""

    DONE = "done"
    NO_MAJORITY = "no_majority"
    NEGATIVE = "negative"
    NONE = "none"
    CHECK_TIMEOUT = "validate_timeout"

class CheckSafeExistenceRound(VotingRound):
    """A round in a which the safe address is validated"""

    round_id = "check_safe_existence"
    allowed_tx_type = SafeExistencePayload.transaction_type
    payload_attribute = "vote"
    done_event = Event.DONE
    negative_event = Event.NEGATIVE
    none_event = Event.NONE
    no_majority_event = Event.NO_MAJORITY
    collection_key = "participant_to_votes"