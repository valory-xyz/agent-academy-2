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

from typing import Set, Type, cast, Generator

from packages.valory.skills.abstract_round_abci.base import BasePeriodState

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

from packages.keep3r_co.skills.keep3r_abci.payloads import (
    SafeExistencePayload,
)

from packages.keep3r_co.skills.keep3r_abci.rounds import (
    CheckSafeExistenceRound,
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

class CheckSafeExistenceBehaviour(BaseState):
    """Check Safe contract existence."""

    state_id = "check_safe_existence"
    matching_round = CheckSafeExistenceRound

    @property
    def period_state(self) -> BasePeriodState:
        """Return the period state."""
        return cast(BasePeriodState, super().period_state)

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - Check if any safe contract is deployed already
        - Wait until ABCI application transitions to the next round.
        - Go to the next behaviour state (set done event).
        """

        with self.context.benchmark_tool.measure(self.state_id).local():
            exists = yield from self.safe_contract_exists()
            payload = SafeExistencePayload(self.context.agent_address, exists)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def safe_contract_exists(self) -> Generator[None, None, bool]:
        """Check Contract deployment verification."""

        if (
            self.period_state.safe_contract_address == None
        ):  # pragma: nocover
            self.context.logger.warning("Safe contract has not been deployed!")
            return False
        
        return True