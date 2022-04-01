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
from typing import Generator, Set, Type, cast

from packages.gabrielfu.contracts.keep3r_job.contract import Keep3rJobContract
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.keep3r_co.skills.keep3r_bot_9k_abci.models import Params, SharedState
from packages.keep3r_co.skills.keep3r_bot_9k_abci.payloads import (
    IsWorkablePayload,
)
from packages.keep3r_co.skills.keep3r_bot_9k_abci.rounds import (
    PeriodState,
    IsWorkableRound,
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


class IsWorkableBehaviour(Keep3rBotABCIBaseState):
    """Check whether the job contract is workable."""
    # TODO: unfinished

    state_id = "is_workable"
    matching_round = IsWorkableRound

    def async_act(self) -> Generator:
        """
        """
        with self.context.benchmark_tool.measure(self.state_id).local():
            self.context.logger.info(
                "I am the designated sender, deploying the safe contract..."
            )
            is_workable = yield from self._get_workable()
            if is_workable is None:
                # The safe_deployment_abci app should only be used in staging.
                # If the safe contract deployment fails we abort. Alternatively,
                # we could send a None payload and then transition into an appropriate
                # round to handle the deployment failure.
                raise RuntimeError("Safe deployment failed!")  # pragma: nocover
            payload = IsWorkablePayload(self.context.agent_address, is_workable)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Job contract is workable {self.context.params.job_contract_address}: {is_workable}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_workable(self):
        # TODO: unfinished
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_STATE,  # type: ignore
            contract_address=self.context.params.job_contract_address,
            contract_id=str(Keep3rJobContract.contract_id),
            contract_callable="get_workable",
        )
        return contract_api_response


class Keep3rBotAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the keep3r bot abci app."""

    initial_state_cls: Keep3rBotABCIBaseState
    abci_app_cls = Keep3rBotAbciApp  # type: ignore
    behaviour_states: Set[Type[Keep3rBotABCIBaseState]] = {  # type: ignore
        IsWorkableBehaviour,  # type: ignore
    }
