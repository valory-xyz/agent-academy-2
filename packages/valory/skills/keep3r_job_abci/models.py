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
"""This module contains the shared state for the 'keep3r_job_abci' application."""

from typing import Any, Dict, List, Type

from aea.configurations.data_types import PublicId

from packages.valory.skills.abstract_round_abci.base import AbciApp
from packages.valory.skills.abstract_round_abci.models import ApiSpecs, BaseParams
from packages.valory.skills.abstract_round_abci.models import (
    BenchmarkTool as BaseBenchmarkTool,
)
from packages.valory.skills.abstract_round_abci.models import Requests as BaseRequests
from packages.valory.skills.abstract_round_abci.models import (
    SharedState as BaseSharedState,
)
from packages.valory.skills.keep3r_job_abci.rounds import Keep3rJobAbciApp


MARGIN = 5


Requests = BaseRequests
BenchmarkTool = BaseBenchmarkTool


class SharedState(BaseSharedState):
    """Keep the current shared state of the skill."""

    abci_app_cls: Type[AbciApp] = Keep3rJobAbciApp

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the shared state object."""
        self.job_address_to_public_id: Dict[str, PublicId] = {}
        super().__init__(*args, **kwargs)


class Params(BaseParams):  # pylint: disable=too-many-instance-attributes
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
        self.supported_jobs_to_package_hash = self._get_supported_jobs_to_package_hash(
            kwargs
        )
        self.use_flashbots = self._ensure("use_flashbots", kwargs, bool)
        self.manual_gas_limit = self._ensure("manual_gas_limit", kwargs, int)
        self.raise_on_failed_simulation = self._ensure(
            "raise_on_failed_simulation", kwargs, bool
        )
        super().__init__(*args, **kwargs)

    def _get_supported_jobs_to_package_hash(self, kwargs: Dict) -> Dict[str, str]:
        """Get the supported jobs to package hash from the kwargs."""
        supported_jobs_to_package_hash = self._ensure(
            "supported_jobs_to_package_hash", kwargs, List[List[str]]
        )
        if len(supported_jobs_to_package_hash) == 0:
            raise ValueError("No supported jobs specified!")
        return {value[0]: value[1] for value in supported_jobs_to_package_hash}


class RandomnessApi(ApiSpecs):
    """A model that wraps ApiSpecs for randomness api specifications."""
