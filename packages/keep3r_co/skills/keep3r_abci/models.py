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

"""This module contains the shared state for the price estimation app ABCI application."""
import logging
import time
from typing import Any

from packages.keep3r_co.skills.keep3r_abci.composition import Keep3rAbciApp
from packages.keep3r_co.skills.keep3r_job.models import Params as Keep3rJobParams
from packages.keep3r_co.skills.keep3r_job.rounds import Event as Keep3rJobEvent
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.registration_abci.rounds import Event as RegistrationEvent
from packages.valory.skills.reset_pause_abci.rounds import Event as ResetPauseEvent
from packages.valory.skills.safe_deployment_abci.rounds import Event as SafeEvent
from packages.valory.skills.transaction_settlement_abci.rounds import Event as TSEvent


MARGIN = 5
MULTIPLIER = 2

Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool
Params = Keep3rJobParams


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=Keep3rAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()

        timeouts = Keep3rAbciApp.event_to_timeout

        round_timeout_seconds = self.context.params.round_timeout_seconds
        validate_timeout = self.context.params.validate_timeout
        finalize_timeout = self.context.params.finalize_timeout
        deploy_timeout = self.context.params.keeper_timeout + MARGIN
        reset_timeout = round_timeout_seconds * MULTIPLIER
        reset_and_pause_timeout = self.context.params.observation_interval + MARGIN

        # ROUND_TIMEOUT
        for event in (
            RegistrationEvent.ROUND_TIMEOUT,
            SafeEvent.ROUND_TIMEOUT,
            Keep3rJobEvent.ROUND_TIMEOUT,
            TSEvent.ROUND_TIMEOUT,
            ResetPauseEvent.ROUND_TIMEOUT,
        ):
            timeouts[event] = round_timeout_seconds

        # RESET_TIMEOUTS
        for event in (Keep3rJobEvent.RESET_TIMEOUT, TSEvent.RESET_TIMEOUT):
            timeouts[event] = reset_timeout

        # FINALIZE_TIMEOUT
        timeouts[TSEvent.FINALIZE_TIMEOUT] = finalize_timeout

        # VALIDATE_TIMEOUT
        for event in (SafeEvent.VALIDATE_TIMEOUT, TSEvent.VALIDATE_TIMEOUT):
            timeouts[event] = validate_timeout

        # DEPLOY_TIMEOUT
        timeouts[SafeEvent.DEPLOY_TIMEOUT] = deploy_timeout

        # RESET_AND_PAUSE_TIMEOUT
        timeouts[ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT] = reset_and_pause_timeout
