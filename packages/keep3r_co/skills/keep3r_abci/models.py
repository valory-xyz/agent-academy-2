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
        Keep3rAbciApp.event_to_timeout[
            Keep3rJobEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rAbciApp.event_to_timeout[
            SafeEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rAbciApp.event_to_timeout[
            Keep3rJobEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rAbciApp.event_to_timeout[
            TSEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rAbciApp.event_to_timeout[
            ResetPauseEvent.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rAbciApp.event_to_timeout[TSEvent.RESET_TIMEOUT] = (
            self.context.params.round_timeout_seconds * MULTIPLIER
        )
        Keep3rAbciApp.event_to_timeout[ResetPauseEvent.RESET_AND_PAUSE_TIMEOUT] = (
            self.context.params.observation_interval + MARGIN
        )