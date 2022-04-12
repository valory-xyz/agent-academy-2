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

"""This module contains the behaviours for the 'abci' skill."""

from typing import Set, Type

from packages.keep3r_co.skills.keep3r_job.behaviours import (
    Keep3rJobAbciApp,
    Keep3rJobRoundBehaviour,
)
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.registration_abci.behaviours import (
    AgentRegistrationRoundBehaviour,
    RegistrationStartupBehaviour,
)
from packages.valory.skills.reset_pause_abci.behaviours import (
    ResetPauseABCIConsensusBehaviour,
)


class Keep3rAbciAppConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the price estimation."""

    initial_state_cls = RegistrationStartupBehaviour
    abci_app_cls = Keep3rJobAbciApp  # type: ignore
    behaviour_states: Set[Type[BaseState]] = {
        *AgentRegistrationRoundBehaviour.behaviour_states,
        *Keep3rJobRoundBehaviour.behaviour_states,
        *ResetPauseABCIConsensusBehaviour.behaviour_states,
    }