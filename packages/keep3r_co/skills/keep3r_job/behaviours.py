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

"""This module contains the behaviours for the 'keep3r_job' skill."""

from abc import ABC
from typing import Generator, Optional, Set, Type, cast

from packages.gabrielfu.contracts.keep3r_job.contract import Keep3rJobContract
from packages.keep3r_co.skills.keep3r_job.models import Params
from packages.keep3r_co.skills.keep3r_job.payloads import TXHashPayload
from packages.keep3r_co.skills.keep3r_job.rounds import (
    Keep3rJobAbciApp,
    PeriodState,
    PrepareTxRound,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.behaviours import (
    AbstractRoundBehaviour,
    BaseState,
)


class Keep3rJobAbciBaseState(BaseState, ABC):
    """Base state behaviour for the simple abci skill."""

    @property
    def period_state(self) -> PeriodState:
        """Return the period state."""
        return cast(PeriodState, super().period_state)

    @property
    def params(self) -> Params:
        """Return the params."""
        return cast(Params, self.context.params)


class PrepareTxBehaviour(Keep3rJobAbciBaseState):
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
            payload = TXHashPayload(self.context.agent_address, tx_hash)

        with self.context.benchmark_tool.measure(self.state_id).consensus():
            self.context.logger.info(f"Safe transaction hash: {tx_hash}")
            yield from self.send_a2a_transaction(payload)
            yield from self.wait_until_round_end()

        self.set_done()

    def _get_raw_work_transaction(self) -> Generator[None, None, Optional[str]]:
        owners = self.period_state.sorted_participants
        contract_api_response = yield from self.get_contract_api_response(
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,  # type: ignore
            contract_address=None,
            contract_id=str(Keep3rJobContract.contract_id),
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


class Keep3rJobRoundBehaviour(AbstractRoundBehaviour):
    """This behaviour manages the consensus stages for the preparetx abci app."""

    initial_state_cls = PrepareTxBehaviour  # type: ignore
    abci_app_cls = Keep3rJobAbciApp  # type: ignore
    behaviour_states: Set[Type[Keep3rJobAbciBaseState]] = {  # type: ignore
        PrepareTxBehaviour,  # type: ignore
    }
