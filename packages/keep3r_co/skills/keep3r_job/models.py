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

from typing import Any, List, Dict

from packages.keep3r_co.skills.keep3r_job.rounds import Keep3rJobAbciApp
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

    abci_app_cls = Keep3rJobAbciApp


class Params(BaseParams):
    """Parameters."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the parameters object."""
        self.job_contract_addresses = self._ensure(
            "job_contract_addresses", kwargs, List[str]
        )
        self.keep3r_v1_contract_address = self._ensure(
            "keep3r_v1_contract_address", kwargs, str
        )
        self.keep3r_v2_contract_address = self._ensure(
            "keep3r_v2_contract_address", kwargs, str
        )
        self.insufficient_funds_threshold = self._ensure(
            "insufficient_funds_threshold", kwargs, int
        )
        self.profitability_threshold = self._ensure(
            "profitability_threshold", kwargs, int
        )
        self.bonding_asset = self._ensure("bonding_asset", kwargs, str)
        self.bond_amount = self._ensure("bond_amount", kwargs, int)
        self.use_v2 = self._ensure("use_v2", kwargs, bool)
        self.supported_jobs = self._ensure("supported_jobs", kwargs, Dict[str, str])
        super().__init__(*args, **kwargs)


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""
