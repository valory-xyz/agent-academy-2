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
from typing import Any, Dict, Optional, Type, cast

import pytest
from aea.helpers.transaction.base import RawTransaction

from packages.keep3r_co.skills.keep3r_job.behaviours import (
    BondingBehaviour,
    GetJobsBehaviour,
    IsProfitableBehaviour,
    IsWorkableBehaviour,
    JobSelectionBehaviour,
    Keep3rJobRoundBehaviour,
    PathSelectionBehaviour,
)
from packages.keep3r_co.skills.keep3r_job.behaviours import (
    PerformWorkBehaviour as PrepareTxBehaviour,
)
from packages.keep3r_co.skills.keep3r_job.behaviours import WaitingBehaviour
from packages.keep3r_co.skills.keep3r_job.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    ActivationRound,
    AwaitTopUpRound,
    BlacklistedRound,
    BondingRound,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    DegenerateRound as NothingToDoRound,
)
from packages.keep3r_co.skills.keep3r_job.rounds import Event, FinalizeBondingRound
from packages.keep3r_co.skills.keep3r_job.rounds import (
    FinalizeWorkRound as FinishedPrepareTxRound,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    GetJobsRound,
    IsProfitableRound,
    JobSelectionRound,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    PerformWorkRound as PrepareTxRound,
)
from packages.keep3r_co.skills.keep3r_job.rounds import SynchronizedData, WaitingRound
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
)
from packages.valory.contracts.keep3r_test_job.contract import (
    PUBLIC_ID as TEST_JOB_CONTRACT_ID,
)
from packages.valory.contracts.keep3r_v1.contract import (
    PUBLIC_ID as KEEP3R_V1_CONTRACT_ID,
)
from packages.valory.protocols.contract_api.custom_types import State
from packages.valory.protocols.contract_api.message import ContractApiMessage
from packages.valory.protocols.ledger_api.message import LedgerApiMessage
from packages.valory.skills.abstract_round_abci.base import AbciAppDB, BaseTxPayload
from packages.valory.skills.abstract_round_abci.behaviour_utils import (
    BaseBehaviour,
    make_degenerate_behaviour,
)
from packages.valory.skills.abstract_round_abci.test_tools.base import (
    FSMBehaviourBaseCase,
)

from tests.conftest import ROOT_DIR
from tests.test_contracts.constants import SECONDS_PER_DAY


AGENT_ADDRESS = "0x1Cc0771e65FC90308DB2f7Fd02482ac4d1B82A18"
SOME_CONTRACT_ADDRESS = "0xaed599aadfee8e32cedb59db2b1120d33a7bacfd"


class DummyRoundId:
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class Keep3rJobFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = Path(ROOT_DIR, "packages", "keep3r_co", "skills", "keep3r_job")

    behaviour: Keep3rJobRoundBehaviour
    ledger_handler: LedgerApiHandler
    http_handler: HttpHandler
    contract_handler: ContractApiHandler
    signing_handler: SigningHandler
    old_tx_type_to_payload_cls: Dict[str, Type[BaseTxPayload]]
    synchronized_data: SynchronizedData
    benchmark_dir: TemporaryDirectory
    done_event = Event.DONE

    behaviour_class: Type[BaseBehaviour]

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the test class."""
        super().setup(**kwargs)
        cls.synchronized_data = SynchronizedData(AbciAppDB(setup_data={}))

    @property
    def current_behaviour(self) -> BaseBehaviour:
        """Current behaviour"""
        return cast(BaseBehaviour, self.behaviour.current_behaviour)

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.behaviour_id,
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert self.current_behaviour.behaviour_id == self.behaviour_class.behaviour_id

    def mock_keep3r_v1_call(self, contract_callable: str, data: Any) -> None:
        """Mock keep3r V1 contract call"""

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=contract_callable,
            ),
            contract_id=str(KEEP3R_V1_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=contract_callable,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": data},
                ),
            ),
        )

    def mock_ethereum_ledger_state_call(self, data: Any) -> None:
        """Mock ethereum ledger get state call"""

        self.mock_ledger_api_request(
            request_kwargs=dict(performative=LedgerApiMessage.Performative.GET_STATE),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.STATE,
                state=State(ledger_id="ethereum", body={"data": data}),
            ),
        )

    def mock_ethereum_get_balance(self, amount: int) -> None:
        """Mock call to ethereum ledger for reading balance"""

        self.mock_ethereum_ledger_state_call(amount)

    def mock_get_latest_block(self, block: Dict[str, Any]) -> None:
        """Mock call to ethereum ledger for getting latest block"""

        return self.mock_ethereum_ledger_state_call(block)


class TestPathSelectionBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test PathSelectionBehaviour"""

    behaviour_class: Type[BaseBehaviour] = PathSelectionBehaviour

    def setup(self, **kwargs: Any) -> None:  # type: ignore
        """Setup"""
        super().setup(**kwargs)
        address = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
        data = dict(safe_contract_address=address)
        self.fast_forward(data)
        self.behaviour.act_wrapper()

    def test_blacklisted(self) -> None:
        """Test path_selection to blacklisted."""

        self.mock_keep3r_v1_call("blacklist", True)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.BLACKLISTED)
        expected = f"degenerate_{BlacklistedRound.round_id}"
        assert self.current_behaviour.behaviour_id == expected

    def test_insufficient_funds(self) -> None:
        """Test path_selection to insufficient funds."""

        self.mock_keep3r_v1_call("blacklist", False)
        self.mock_ethereum_get_balance(amount=-1)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.INSUFFICIENT_FUNDS)
        assert self.current_behaviour.behaviour_id == AwaitTopUpRound.round_id

    def test_not_bonded(self) -> None:
        """Test path_selection to not bonded."""

        self.mock_keep3r_v1_call("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_keep3r_v1_call("bondings", 0)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_BONDED)
        assert self.current_behaviour.behaviour_id == BondingRound.round_id

    def test_not_activated(self) -> None:
        """Test path_selection to not activated."""

        self.mock_keep3r_v1_call("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_keep3r_v1_call("bondings", 1)
        self.mock_keep3r_v1_call("BOND", 3 * SECONDS_PER_DAY)
        self.mock_get_latest_block(block={"timestamp": 0})
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_ACTIVATED)
        assert self.current_behaviour.behaviour_id == WaitingRound.round_id

    def test_healthy(self) -> None:
        """Test path_selection to healthy."""

        self.mock_keep3r_v1_call("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_keep3r_v1_call("bondings", 1)
        self.mock_keep3r_v1_call("BOND", 3 * SECONDS_PER_DAY)
        self.mock_get_latest_block(block={"timestamp": 3 * SECONDS_PER_DAY + 1})
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.HEALTHY)
        assert self.current_behaviour.behaviour_id == GetJobsRound.round_id


class TestBondingBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test BondingBehaviour"""

    behaviour_class: Type[BaseBehaviour] = BondingBehaviour

    def setup(self, **kwargs: Any) -> None:  # type: ignore
        """Setup"""
        super().setup(**kwargs)
        self.fast_forward()
        self.behaviour.act_wrapper()

    def test_bonding_tx(self) -> None:
        """Test bonding tx"""

        self.mock_keep3r_v1_call("build_bond_tx", {})
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.BONDING_TX)
        expected = f"degenerate_{FinalizeBondingRound.round_id}"
        assert self.current_behaviour.behaviour_id == expected


class TestWaitingBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test BondingBehaviour"""

    behaviour_class: Type[BaseBehaviour] = WaitingBehaviour

    def setup(self, **kwargs: Any) -> None:  # type: ignore
        """Setup"""
        super().setup(**kwargs)
        address = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
        data = dict(safe_contract_address=address)
        self.fast_forward(data)
        self.behaviour.act_wrapper()

    def test_waiting(self) -> None:
        """Test waiting"""

        self.mock_keep3r_v1_call("bondings", 0)
        self.mock_keep3r_v1_call("BOND", 1)
        self.mock_get_latest_block(block={"timestamp": 2})
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert self.current_behaviour.behaviour_id == ActivationRound.round_id


class TestGetJobsBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test GetJobsBehaviour"""

    behaviour_class: Type[BaseBehaviour] = GetJobsBehaviour

    def test_get_jobs(self) -> None:
        """Test get_jobs."""

        address = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
        data = dict(keep3r_v1_contract_address=address)
        self.fast_forward(data)

        contract_callable = "get_jobs"
        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=contract_callable,
            ),
            contract_id=str(KEEP3R_V1_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=contract_callable,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": ["some_job_address"]},
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert self.current_behaviour.behaviour_id == JobSelectionRound.round_id


@pytest.mark.skip("ABCIApp redesign: no payment assigned yet")
class TestPrepareTxBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test SelectKeeperBehaviour."""

    prepare_tx_behaviour_class: Type[BaseBehaviour] = PrepareTxBehaviour

    def test_prepare_tx(
        self,
    ) -> None:
        """Test prepare tx."""

        self.fast_forward_to_behaviour(
            self.behaviour,
            self.prepare_tx_behaviour_class.behaviour_id,
            SynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(
                        dict(
                            job_selection="some_job",
                            safe_contract_address=SOME_CONTRACT_ADDRESS,
                        )
                    ),
                ),
            ),
        )
        assert (
            self.current_behaviour.behaviour_id
            == self.prepare_tx_behaviour_class.behaviour_id
        )
        self.behaviour.act_wrapper()

        # first mock the work tx itself

        # then mock the safe tx

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                contract_address=SOME_CONTRACT_ADDRESS,
            ),
            contract_id=str(TEST_JOB_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                callable="work",
                raw_transaction=RawTransaction(
                    ledger_id="ethereum",
                    body={
                        "hash": "stub",
                        "to_address": "to_address",
                        "ether_value": 0,
                        "data": {},
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

        self.behaviour.act_wrapper()

        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        degenerate_state = make_degenerate_behaviour(FinishedPrepareTxRound.round_id)
        assert self.current_behaviour.behaviour_id == degenerate_state.behaviour_id


@pytest.mark.skip("ABCIApp redesign: no payment assigned yet")
class TestJobSelectionBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test JobSelectionBehaviour."""

    job_selection_behaviour_class: Type[BaseBehaviour] = JobSelectionBehaviour

    def test_empty_jobs(self) -> None:
        """Test empty jobs."""
        self.skill.skill_context.params.job_contract_addresses = []
        self.fast_forward_to_behaviour(
            self.behaviour,
            JobSelectionBehaviour.behaviour_id,
            self.synchronized_data,
        )
        assert self.current_behaviour.behaviour_id == JobSelectionBehaviour.behaviour_id

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_WORKABLE)
        state = cast(BaseBehaviour, self.behaviour.current_behaviour)
        expected_behaviour_id = make_degenerate_behaviour(
            NothingToDoRound.round_id
        ).behaviour_id
        assert state.behaviour_id == expected_behaviour_id

    @pytest.mark.parametrize("n_jobs", range(1, 10))
    def test_n_jobs(self, n_jobs: int) -> None:
        """Test n jobs."""
        self.skill.skill_context.params.job_contract_addresses = [
            f"job_contract_{i}" for i in range(1, n_jobs)
        ]

        self.fast_forward_to_behaviour(
            self.behaviour,
            JobSelectionBehaviour.behaviour_id,
            self.synchronized_data,
        )
        assert self.current_behaviour.behaviour_id == JobSelectionBehaviour.behaviour_id

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert self.current_behaviour.behaviour_id == IsWorkableBehaviour.behaviour_id


@pytest.mark.skip("ABCIApp redesign: no payment assigned yet")
class TestIsWorkableBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test IsWorkableBehaviour."""

    CONTRACT_ADDRESS: str = "contract_address"
    CONTRACT_CALLABLE: str = "get_workable"
    is_workable_behaviour_class: Type[BaseBehaviour] = IsWorkableBehaviour

    def test_is_workable_true(self) -> None:
        """Test is workable true."""
        self.skill.skill_context.params.job_contract_addresses = ["job_contract_1"]
        self.fast_forward_to_behaviour(
            self.behaviour,
            IsWorkableBehaviour.behaviour_id,
            SynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict(job_selection="some_job"))
                )
            ),
        )
        assert self.current_behaviour.behaviour_id == IsWorkableBehaviour.behaviour_id

        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=self.CONTRACT_CALLABLE,
            ),
            contract_id=str(TEST_JOB_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=self.CONTRACT_CALLABLE,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": True},
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert self.current_behaviour.behaviour_id == IsProfitableRound.round_id

    def test_is_workable_false(self) -> None:
        """Test is workable false."""
        self.fast_forward_to_behaviour(
            self.behaviour,
            IsWorkableBehaviour.behaviour_id,
            SynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict(job_selection="some_job"))
                )
            ),
        )
        assert self.current_behaviour.behaviour_id == IsWorkableBehaviour.behaviour_id

        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=self.CONTRACT_CALLABLE,
            ),
            contract_id=str(TEST_JOB_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=self.CONTRACT_CALLABLE,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": False},
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_WORKABLE)
        degenerate_state = make_degenerate_behaviour(NothingToDoRound.round_id)
        assert self.current_behaviour.behaviour_id == degenerate_state.behaviour_id


@pytest.mark.skip("ABCIApp redesign: no payment assigned yet")
class TestIsProfitableBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test IsProfitableBehaviour."""

    CONTRACT_ADDRESS: str = "contract_address"
    CONTRACT_CALLABLE: str = "rewardMultiplier"
    is_profitable_behaviour_class: Type[BaseBehaviour] = IsProfitableBehaviour

    def test_is_profitable_true(self) -> None:
        """Test is profitable true."""
        self.skill.skill_context.params.job_contract_addresses = ["job_contract_1"]
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.is_profitable_behaviour_class.behaviour_id,
            SynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict(job_selection="some_job"))
                )
            ),
        )

        assert self.current_behaviour.behaviour_id == IsProfitableBehaviour.behaviour_id

        self.behaviour.context.params.profitability_threshold = 100
        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            contract_id=str(TEST_JOB_CONTRACT_ID),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=self.CONTRACT_CALLABLE,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=self.CONTRACT_CALLABLE,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"rewardMultiplier": 90},
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert self.current_behaviour.behaviour_id == PrepareTxRound.round_id

    def test_is_profitable_false(self) -> None:
        """Test is profitable false."""
        self.skill.skill_context.params.job_contract_addresses = ["job_contract_1"]
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.is_profitable_behaviour_class.behaviour_id,
            SynchronizedData(
                AbciAppDB(
                    setup_data=AbciAppDB.data_to_lists(dict(job_selection="some_job"))
                )
            ),
        )
        assert self.current_behaviour.behaviour_id == IsProfitableBehaviour.behaviour_id

        self.behaviour.context.params.profitability_threshold = 100
        self.behaviour.act_wrapper()
        self.mock_contract_api_request(
            contract_id=str(TEST_JOB_CONTRACT_ID),
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=self.CONTRACT_CALLABLE,
            ),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=self.CONTRACT_CALLABLE,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"rewardMultiplier": 110},
                ),
            ),
        )
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_PROFITABLE)
        degenerate_state = make_degenerate_behaviour(NothingToDoRound.round_id)
        assert self.current_behaviour.behaviour_id == degenerate_state.behaviour_id
