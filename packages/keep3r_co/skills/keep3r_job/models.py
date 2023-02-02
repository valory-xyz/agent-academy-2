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

"""This module contains the shared state for the 'keep3r_job' application."""

from typing import Any

from packages.keep3r_co.skills.keep3r_job.rounds import Event, Keep3rJobAbciApp
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)


MARGIN = 5


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the state."""
        super().__init__(*args, abci_app_cls=Keep3rJobAbciApp, **kwargs)

    def setup(self) -> None:
        """Set up."""
        super().setup()
        Keep3rJobAbciApp.event_to_timeout[
            Event.ROUND_TIMEOUT
        ] = self.context.params.round_timeout_seconds
        Keep3rJobAbciApp.event_to_timeout[Event.ROUND_TIMEOUT] = (
            self.context.params.observation_interval + MARGIN
        )


class Params(BaseParams):
    """Parameters."""

    required = [
        "job_contract_addresses",
        "keep3r_v1_contract_address",
        "keep3r_v2_contract_address",
        "insufficient_funds_threshold",
        "profitability_threshold",
        "bonding_asset",
        "bond_amount",
        "use_v2",
    ]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""

        for item in self.required:
            setattr(self, item, self._ensure(item, kwargs))
        super().__init__(*args, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""
