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

"""This module contains the shared state for the price estimation app ABCI application."""

from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.keep3r_abci.composition import Keep3rAbciApp
from packages.valory.skills.keep3r_job_abci.models import Params as Keep3rJobParams
from packages.valory.skills.keep3r_job_abci.models import (
    RandomnessApi as BaseRandomnessApi,
)
from packages.valory.skills.keep3r_job_abci.models import (
    SharedState as Keep3rJobSharedState,
)
from packages.valory.skills.keep3r_job_abci.rounds import Event as Keep3rJobEvent
from packages.valory.skills.registration_abci.rounds import Event as RegistrationEvent
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetPauseEvent
from packages.valory.skills.termination_abci.models import TerminationParams
from packages.valory.skills.transaction_settlement_abci.rounds import Event as TSEvent


MARGIN = 5
MULTIPLIER = 2

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
RandomnessApi = BaseRandomnessApi


class SharedState(Keep3rJobSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls = Keep3rAbciApp

    def setup(self) -> None:  # pylint: disable=too-many-instance-attributes
        """Set up."""
        super().setup()
        timeouts = Keep3rAbciApp.event_to_timeout
        round_timeout_seconds = self.context.params.round_timeout_seconds
        validate_timeout = self.context.params.validate_timeout
        finalize_timeout = self.context.params.finalize_timeout
        reset_timeout = round_timeout_seconds * MULTIPLIER
        reset_and_pause_timeout = self.context.params.reset_pause_duration + MARGIN

        # ROUND_TIMEOUT
        for event in (
            RegistrationEvent.ROUND_TIMEOUT,
            Keep3rJobEvent.ROUND_TIMEOUT,
            TSEvent.ROUND_TIMEOUT,
            ResetPauseEvent.ROUND_TIMEOUT,
        ):
            timeouts[event] = round_timeout_seconds

        # RESET_TIMEOUTS
        timeouts[TSEvent.RESET_TIMEOUT] = reset_timeout

        # FINALIZE_TIMEOUT
        timeouts[TSEvent.FINALIZE_TIMEOUT] = finalize_timeout

        # VALIDATE_TIMEOUT
        for event in (TSEvent.VALIDATE_TIMEOUT,):
            timeouts[event] = validate_timeout

        # RESET_AND_PAUSE_TIMEOUT
        timeouts[ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT] = reset_and_pause_timeout


class Params(Keep3rJobParams, TerminationParams):
    """Parameters for the skill."""
