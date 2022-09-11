# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains helper classes/functions for fixtures."""

from typing import Any, List, Tuple

import pytest
from aea_test_autonomy.configurations import KEY_PAIRS


@pytest.mark.integration
class UseHardHatKeep3rBaseTest:
    """Inherit from this class to use HardHat local net with the Keep3r contracts deployed."""

    key_pairs: List[Tuple[str, str]] = KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True)
    def _start_hardhat(
        cls,
        hardhat_keep3r_scope_function: Any,
        hardhat_keep3r_addr: Any,
        hardhat_keep3r_key_pairs: Any,
        # TODO: setup_job_contracts: Any,
    ) -> None:
        """Start a HardHat ElCol instance."""
        cls.key_pairs = hardhat_keep3r_key_pairs
