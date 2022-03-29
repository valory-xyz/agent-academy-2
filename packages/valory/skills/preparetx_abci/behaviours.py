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

"""This module contains the behaviours for the 'simple_abci' skill."""

from abc import ABC
from math import floor
from typing import Generator, List, Set, Type, cast

from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)
from packages.valory.skills.simple_abci.models import Params, SharedState
from packages.valory.skills.simple_abci.payloads import (
    RandomnessPayload,
    RegistrationPayload,
    ResetPayload,
    SelectKeeperPayload,
    PrepareTxPayload
)
from packages.valory.skills.simple_abci.rounds import (
    PeriodState,
    RandomnessStartupRound,
    RegistrationRound,
    ResetAndPauseRound,
    SelectKeeperAtStartupRound,
    SimpleAbciApp,
    PrepareTxRound
)

from packages.valory.contracts.keeper.contract import KeeperContract

class PrepareTxABCIBaseState(BaseState, ABC):
    """Base state behaviour for the simple abci skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, cast(SharedState, self.context.state).period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)

class PrepareTxBehaviour(PrepareTxABCIBaseState):
    """Deploy Safe."""

    state_id = "prepare_tx"
    matching_round = PrepareTxRound

    def async_act(self) -> Generator:
        """
        Do the action.

        Steps:
        - If the agent is the designated deployer, then prepare the deployment
          transaction and send it.
        - Otherwise, wait until the next round.
        - If a timeout is hit, set exit A event, otherwise set done event.
        """
        with self.context.benchmark_tool.measure(self.state_id).local():
        
            tx_hash = yield from self._get_raw_work_transaction()
            if tx_hash is None:
                # The safe_deployment_abci app should only be used in staging.
                # If the safe contract deployment fails we abort. Alternatively,
                # we could send a None payload and then transition into an appropriate
                # round to handle the deployment failure.
                raise RuntimeError("Work transaction deployment failed!")  # pragma: nocover
            payload = PrepareTxPayload(self.context.agent_address, tx_hash)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Safe transaction hash: {tx_hash}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_raw_work_transaction(self) -> Generator[None, None, Optional[str]]:
        owners = self.period_state.sorted_participants
        threshold = self.params.consensus_params.consensus_threshold
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,  # type: ignore
            contract_address=None,
            contract_id=str(KeeperContract.contract_id),
            contract_callable="get_raw_work_transaction",
            job_contract_address=self.context.param.job_contract_address,
            sender_address=self.context.agent_address,
            owners=owners,
            signatures_by_owner={
                key: payload.signature
                for key, payload in self.period_state.participant_to_signature.items()
            }
        )
        if (
            contract_api_response.performative
            != ContractApiMessage.Performative.RAW_TRANSACTION
        ):  # pragma: nocover
            self.context.logger.warning("Get work transaction unsuccessful!")
            return None
        tx_hash = cast(
            str, contract_api_response.raw_transaction.body.pop("hash")
        )
        
        return tx_hash

    # def _deploy_work_transaction(self) -> Generator[None, None, Optional[str]]:
    #     owners = self.period_state.sorted_participants
    #     threshold = self.params.consensus_params.consensus_threshold
    #     contract_api_response = yield from self.get_contract_api_response(
    #         performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,  # type: ignore
    #         contract_address=None,
    #         contract_id=str(KeeperContract.contract_id),
    #         contract_callable="get_raw_work_transaction",
    #         job_contract_address=self.context.param.job_contract_address,
    #     )
    #     if (
    #         contract_api_response.performative
    #         != ContractApiMessage.Performative.RAW_TRANSACTION
    #     ):  # pragma: nocover
    #         self.context.logger.warning("Deploy work transaction unsuccessful!")
    #         return None
    #     tx_hash = cast(
    #         str, contract_api_response.raw_transaction.body.pop("hash")
    #     )
        
    #     return tx_hash


class PrepareTxAbciConsensusBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the preparetx abci app."""

    initial_state_cls = PrepareTxBehaviour
    abci_app_cls = PrepareTxAbciApp  # type: ignore
    behaviour_states: Set[Type[PrepareTxABCIBaseState]] = {  # type: ignore
        PrepareTxBehaviour,  # type: ignore
    }
