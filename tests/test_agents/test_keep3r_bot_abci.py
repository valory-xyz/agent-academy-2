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

"""End2end tests for the keep3r_co/keep3r_abci skill."""

import pytest

from tests.test_agents.base import BaseTestEnd2EndExecution


# check log messages of the happy path
CHECK_STRINGS = (
    "Entered in the 'registration_startup' round for period 0",
    "'registration' round is done",
    "Entered in the 'is_workable' round for period 0",
    "'is_workable' round is done",
    "Entered in the 'prepare_tx' round for period 0",
    "'prepare_tx' round is done",
    "Entered in the 'reset_and_pause' round for period 0",
    "'reset_and_pause' round is done",
    "Period end",
    "Entered in the 'registration' round for period 1",
    "Entered in the 'reset_and_pause' round for period 1",
)


class BaseKeep3rABCITest(BaseTestEnd2EndExecution):
    """BaseKeep3rABCITest"""

    agent_package = "keep3r_co/keep3r_bot:0.1.0"
    skill_package = "keep3r_co/keep3r_abci:0.1.0"
    wait_to_finish = 80
    check_strings = CHECK_STRINGS


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (1,))
class TestKeep3rABCISingleAgent(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with only one agent."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (2,))
class TestKeep3rABCITwoAgents(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with two agents."""


@pytest.mark.e2e
@pytest.mark.parametrize("nb_nodes", (4,))
class TestKeep3rABCIFourAgents(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with four agents."""
