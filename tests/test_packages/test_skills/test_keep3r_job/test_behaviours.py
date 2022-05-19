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

"""Tests for valory/keep3r_job skill's behaviours."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Type, cast

from aea.helpers.transaction.base import RawTransaction

from packages.gabrielfu.contracts.keep3r_job.contract import PUBLIC_ID as CONTRACT_ID
from packages.keep3r_co.skills.keep3r_job.behaviours import (
    Keep3rJobRoundBehaviour,
    PrepareTxBehaviour,
)
from packages.keep3r_co.skills.keep3r_job.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    Event,
    FinishedPrepareTxRound,
    PeriodState,
)
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.skills.abstract_round_abci.base import BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseState,
    make_degenerate_state,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_simple_abci.test_behaviours import (
    FSMBehaviourBaseCase,
)


class DummyRoundId:
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class Keep3rJobFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(ROOT_DIR, "packages", "keep3r_co", "skills", "keep3r_job")

    abci_behaviour: Keep3rJobRoundBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    period_state: PeriodState
    benchmark_dir: TemporaryDirectory
    done_event = Event.DONE


class TestPrepareTxBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test SelectKeeperBehaviour."""

    preparetx_behaviour_class: Type[BaseState] = PrepareTxBehaviour

    def test_preparetx(
        self,
    ) -> None:
        """Test prepare tx."""
        self.fast_forward_to_state(
            self.abci_behaviour,
            self.preparetx_behaviour_class.state_id,
            self.period_state,
        )
        assert (
            cast(
                BaseState,
                cast(BaseState, self.abci_behaviour.current_state),
            ).state_id
            == self.preparetx_behaviour_class.state_id
        )
        self.abci_behaviour.act_wrapper()

        # first mock the work tx itself

        # then mock the safe tx

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="work",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={
                        "hash": "stub",
                        "to_address": "to_address",
                        "ether_value": 0,
                        "data": b"",
                        "safe_tx_gas": 2100000,
                        "operation": "call",
                    },
                ),
            ),
        )
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="get_raw_safe_transaction_hash",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={
                        "tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                    },
                ),
            ),
        )

        self.abci_behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round()
        state = cast(BaseState, self.abci_behaviour.current_state)
        assert (
            state.state_id
            == make_degenerate_state(FinishedPrepareTxRound.round_id).state_id
        )
