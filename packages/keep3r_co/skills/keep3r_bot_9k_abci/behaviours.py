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

"""This module contains the behaviours for the 'Keep3r Bot' skill."""

from abc import ABC
from typing import Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.keep3r_co.skills.keep3r_bot_9k_abci.models import Params, SharedState
from packages.keep3r_co.skills.keep3r_bot_9k_abci.rounds import (
    PeriodState,
    Keep3rBotAbciApp,
)


class Keep3rBotABCIBaseState(BaseState, ABC):
    """Base state behaviour for the Keep3r Bot skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class Keep3rBotAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the keep3r bot abci app."""

    initial_state_cls: Keep3rBotABCIBaseState
    abci_app_cls = Keep3rBotAbciApp  # type: ignore
    behaviour_states: Set[Type[Keep3rBotABCIBaseState]] = {}  # type: ignore

