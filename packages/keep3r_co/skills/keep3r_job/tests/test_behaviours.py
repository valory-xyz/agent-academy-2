# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

from tempfile import TemporaryDirectory
from typing import Any, Dict, Optional, Type, cast
from unittest import mock

import pytest

from packages.keep3r_co.skills.keep3r_job.behaviours import (
    ActivationBehaviour,
    ApproveBondBehaviour,
    AwaitTopUpBehaviour,
    BondingBehaviour,
    GetJobsBehaviour,
    IsProfitableBehaviour,
    IsWorkableBehaviour,
    JobSelectionBehaviour,
    Keep3rJobRoundBehaviour,
    PathSelectionBehaviour,
    PerformWorkBehaviour,
    SAFE_GAS,
    SafeTx,
    WaitingBehaviour,
    ZERO_ETH,
)
from packages.keep3r_co.skills.keep3r_job.handlers import (
    ContractApiHandler,
    HttpHandler,
    LedgerApiHandler,
    SigningHandler,
)
from packages.keep3r_co.skills.keep3r_job.rounds import (
    ActivationRound,
    ApproveBondRound,
    AwaitTopUpRound,
    BlacklistedRound,
    BondingRound,
    Event,
    FinalizeActivationRound,
    FinalizeApproveBondRound,
    FinalizeBondingRound,
    FinalizeWorkRound,
    GetJobsRound,
    IsProfitableRound,
    IsWorkableRound,
    JobSelectionRound,
    Keep3rJobAbstractRound,
    PathSelectionRound,
    PerformWorkRound,
    SynchronizedData,
    WaitingRound,
)
from packages.keep3r_co.skills.keep3r_job.tests import PACKAGE_DIR
from packages.keep3r_co.skills.keep3r_job.tests.helpers import (
    DUMMY_CONTRACT_PACKAGE,
    wrap_dummy_get_from_ipfs,
)
from packages.valory.contracts.gnosis_safe.contract import (
    PUBLIC_ID as GNOSIS_SAFE_CONTRACT_ID,
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


SECONDS_PER_DAY = 24 * 60 * 60
AGENT_ADDRESS = "0x1Cc0771e65FC90308DB2f7Fd02482ac4d1B82A18"
SOME_CONTRACT_ADDRESS = "0xaed599aadfee8e32cedb59db2b1120d33a7bacfd"
DUMMY_DATA = (
    "0x7cf5dab00000000000000000000000000000000000000000000000000000000000000005"
)
DUMMY_SAFE_TX: SafeTx = {
    "to": SOME_CONTRACT_ADDRESS,
    "data": bytes.fromhex(DUMMY_DATA[2:]),
    "value": ZERO_ETH,
    "gas": SAFE_GAS,
}
TEST_JOB_CONTRACT_ID = "test_job_contract_id"
DUMMY_CONTRACT = "0xaed599aadfee8e32cedb59db2b1120d33a7bacfd"


class DummyRoundId:  # pylint: disable=too-few-public-methods
    """Dummy class for setting round_id for exit condition."""

    round_id: str

    def __init__(self, round_id: str) -> None:
        """Dummy class for setting round_id for exit condition."""
        self.round_id = round_id


class Keep3rJobFSMBehaviourBaseCase(FSMBehaviourBaseCase):
    """Base test case."""

    path_to_skill = PACKAGE_DIR

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

    def setup(self, **kwargs: Any) -> None:  # type: ignore
        """Setup"""
        super().setup(**kwargs)
        data = dict(
            keep3r_v1_contract_address=SOME_CONTRACT_ADDRESS,
            safe_contract_address=SOME_CONTRACT_ADDRESS,
            job_list=[SOME_CONTRACT_ADDRESS],
            current_job=SOME_CONTRACT_ADDRESS,
        )
        self.fast_forward(data)

    @property
    def current_behaviour(self) -> BaseBehaviour:
        """Current behaviour"""
        return cast(BaseBehaviour, self.behaviour.current_behaviour)

    def fast_forward(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Fast-forward"""

        data = data if data is not None else {}
        self.fast_forward_to_behaviour(
            self.behaviour,
            self.behaviour_class.auto_behaviour_id(),
            SynchronizedData(AbciAppDB(setup_data=AbciAppDB.data_to_lists(data))),
        )
        assert (
            self.current_behaviour.auto_behaviour_id()
            == self.behaviour_class.auto_behaviour_id()
        )

    def mock_read_keep3r_v1(self, contract_callable: str, data: Any) -> None:
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

    def mock_keep3r_v1_raw_tx(self, contract_callable: str, data: Any) -> None:
        """Mock keep3r V1 raw transaction"""

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

    def mock_workable_call(self, data: bool) -> None:
        """Mock TestJob workable contract call"""

        contract_callable = "workable"
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=contract_callable,
            ),
            contract_id=str(TEST_JOB_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=contract_callable,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": data},
                ),
            ),
        )

    def mock_build_work_tx_call(self, data: str) -> None:
        """Mock build work transaction"""

        contract_callable = "build_work_tx"
        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
                callable=contract_callable,
            ),
            contract_id=str(TEST_JOB_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable=contract_callable,
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={"data": data},  # type: ignore
                ),
            ),
        )

    def mock_build_safe_raw_tx(self) -> None:
        """Mock build safe raw transaction"""

        self.mock_contract_api_request(
            request_kwargs=dict(
                performative=ContractApiMessage.Performative.GET_STATE,
            ),
            contract_id=str(GNOSIS_SAFE_CONTRACT_ID),
            response_kwargs=dict(
                performative=ContractApiMessage.Performative.STATE,
                callable="get_raw_safe_transaction_hash",
                state=ContractApiMessage.State(
                    ledger_id="ethereum",
                    body={
                        "tx_hash": "0xb0e6add595e00477cf347d09797b156719dc5233283ac76e4efce2a674fe72d9"
                    },
                ),
            ),
        )

    def mock_ethereum_ledger_state_call(self, data: Dict[str, Any]) -> None:
        """Mock ethereum ledger get state call"""

        self.mock_ledger_api_request(
            request_kwargs=dict(performative=LedgerApiMessage.Performative.GET_STATE),
            response_kwargs=dict(
                performative=LedgerApiMessage.Performative.STATE,
                state=State(ledger_id="ethereum", body=data),
            ),
        )

    def mock_ethereum_get_balance(self, amount: int) -> None:
        """Mock call to ethereum ledger for reading balance"""

        self.mock_ethereum_ledger_state_call({"get_balance_result": amount})

    def mock_get_latest_block(self, block: Dict[str, Any]) -> None:
        """Mock call to ethereum ledger for getting latest block"""

        return self.mock_ethereum_ledger_state_call(block)


@mock.patch.object(
    BaseBehaviour,
    "get_from_ipfs",
    side_effect=wrap_dummy_get_from_ipfs(DUMMY_CONTRACT_PACKAGE),
)
class TestPathSelectionBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test PathSelectionBehaviour"""

    behaviour_class: Type[BaseBehaviour] = PathSelectionBehaviour

    def test_blacklisted(self, *_: Any) -> None:
        """Test path_selection to blacklisted."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", True)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.BLACKLISTED)
        degenerate_state = make_degenerate_behaviour(BlacklistedRound)
        assert (
            self.current_behaviour.auto_behaviour_id()
            == degenerate_state.auto_behaviour_id()
        )

    def test_insufficient_funds(self, *_: Any) -> None:
        """Test path_selection to insufficient funds."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", False)
        self.mock_ethereum_get_balance(amount=-1)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.INSUFFICIENT_FUNDS)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == AwaitTopUpRound.auto_round_id()
        )

    def test_not_bonded(self, *_: Any) -> None:
        """Test path_selection to not bonded."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_read_keep3r_v1("bondings", 0)
        self.mock_read_keep3r_v1("allowance", 1000000)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_BONDED)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == BondingRound.auto_round_id()
        )

    def test_not_approved(self, *_: Any) -> None:
        """Test path_selection to not bonded."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_read_keep3r_v1("bondings", 0)
        self.mock_read_keep3r_v1("allowance", 0)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.APPROVE_BOND)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == ApproveBondRound.auto_round_id()
        )

    def test_not_activated(self, *_: Any) -> None:
        """Test path_selection to not activated."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_read_keep3r_v1("bondings", 1)
        self.mock_read_keep3r_v1("bondings", 1)
        self.mock_read_keep3r_v1("bond", 3 * SECONDS_PER_DAY)
        self.mock_get_latest_block(block={"timestamp": 0})
        self.mock_read_keep3r_v1("is_keeper", False)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.NOT_ACTIVATED)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == WaitingRound.auto_round_id()
        )

    def test_healthy(self, *_: Any) -> None:
        """Test path_selection to healthy."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("blacklist", False)
        self.mock_ethereum_get_balance(amount=0)
        self.mock_read_keep3r_v1("bondings", 1)
        self.mock_read_keep3r_v1("bondings", 1)
        self.mock_read_keep3r_v1("bond", 3 * SECONDS_PER_DAY)
        self.mock_get_latest_block({"timestamp": 3 * SECONDS_PER_DAY + 1})
        self.mock_read_keep3r_v1("is_keeper", True)
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.HEALTHY)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == GetJobsRound.auto_round_id()
        )


class TestBondingBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test BondingBehaviour"""

    behaviour_class: Type[BaseBehaviour] = BondingBehaviour

    def test_bonding_tx(self) -> None:
        """Test bonding tx"""
        self.behaviour.act_wrapper()
        self.mock_keep3r_v1_raw_tx("build_bond_tx", DUMMY_DATA)
        self.mock_build_safe_raw_tx()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.BONDING_TX)
        degenerate_state = make_degenerate_behaviour(FinalizeBondingRound)
        assert (
            self.current_behaviour.auto_behaviour_id()
            == degenerate_state.auto_behaviour_id()
        )


class TestWaitingBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test BondingBehaviour"""

    behaviour_class: Type[BaseBehaviour] = WaitingBehaviour

    def test_waiting(self) -> None:
        """Test waiting"""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("bondings", 0)
        self.mock_read_keep3r_v1("bond", 1)
        self.mock_get_latest_block(block={"timestamp": 2})
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == ActivationRound.auto_round_id()
        )


class TestActivationBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test ActivationBehaviour"""

    behaviour_class: Type[BaseBehaviour] = ActivationBehaviour

    def test_activation_tx(self) -> None:
        """Test activation tx"""
        self.behaviour.act_wrapper()
        self.mock_keep3r_v1_raw_tx("build_activate_tx", DUMMY_DATA)
        self.behaviour.act_wrapper()
        self.mock_build_safe_raw_tx()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.ACTIVATION_TX)
        degenerate_state = make_degenerate_behaviour(FinalizeActivationRound)
        assert (
            self.current_behaviour.auto_behaviour_id()
            == degenerate_state.auto_behaviour_id()
        )


class TestApproveBondBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test ApproveBondBehaviour"""

    behaviour_class: Type[BaseBehaviour] = ApproveBondBehaviour

    def test_activation_tx(self) -> None:
        """Test activation tx"""
        self.behaviour.act_wrapper()
        self.mock_keep3r_v1_raw_tx("build_approve_tx", DUMMY_DATA)
        self.behaviour.act_wrapper()
        self.mock_build_safe_raw_tx()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.APPROVE_BOND)
        degenerate_state = make_degenerate_behaviour(FinalizeApproveBondRound)
        assert (
            self.current_behaviour.auto_behaviour_id()
            == degenerate_state.auto_behaviour_id()
        )


class TestGetJobsBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test GetJobsBehaviour"""

    behaviour_class: Type[BaseBehaviour] = GetJobsBehaviour

    def test_get_jobs(self) -> None:
        """Test get_jobs."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("get_jobs", ["some_job_address"])
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.DONE)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == JobSelectionRound.auto_round_id()
        )


class TestPerformWorkBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test PerformWorkBehaviour."""

    behaviour_class: Type[BaseBehaviour] = PerformWorkBehaviour

    def test_run(self) -> None:
        """Test perform work."""
        self.behaviour.context.state.job_address_to_public_id[
            DUMMY_CONTRACT
        ] = TEST_JOB_CONTRACT_ID
        self.behaviour.act_wrapper()
        self.mock_build_work_tx_call(DUMMY_DATA)
        self.mock_build_safe_raw_tx()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=Event.WORK_TX)
        degenerate_state = make_degenerate_behaviour(FinalizeWorkRound)
        assert (
            self.current_behaviour.auto_behaviour_id()
            == degenerate_state.auto_behaviour_id()
        )


class TestJobSelectionBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test JobSelectionBehaviour."""

    behaviour_class: Type[BaseBehaviour] = JobSelectionBehaviour

    @pytest.mark.parametrize(
        "event, next_round",
        [(Event.NO_JOBS, PathSelectionRound), (Event.DONE, IsWorkableRound)],
    )
    def test_get_jobs(self, event: Event, next_round: Keep3rJobAbstractRound) -> None:
        """Test no jobs."""

        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == next_round.auto_round_id()
        )


class TestIsWorkableBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test IsWorkableBehaviour."""

    behaviour_class: Type[BaseBehaviour] = IsWorkableBehaviour

    @pytest.mark.parametrize(
        "is_workable, event, next_round",
        [
            (True, Event.WORKABLE, IsProfitableRound),
            (False, Event.NOT_WORKABLE, JobSelectionRound),
        ],
    )
    def test_is_workable(
        self, is_workable: bool, event: Event, next_round: Keep3rJobAbstractRound
    ) -> None:
        """Test is_workable."""
        with mock.patch.object(
            self.behaviour_class, "sleep", wrap_dummy_get_from_ipfs()
        )
            self.behaviour.context.state.job_address_to_public_id[
                DUMMY_CONTRACT
            ] = TEST_JOB_CONTRACT_ID
            self.behaviour.act_wrapper()
            self.mock_workable_call(is_workable)
            self.behaviour.act_wrapper()
            self.mock_a2a_transaction()
            self._test_done_flag_set()
            self.end_round(done_event=event)
            assert (
                self.current_behaviour.matching_round.auto_round_id()
                == next_round.auto_round_id()
            )


class TestIsProfitableBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test IsProfitableBehaviour."""

    behaviour_class: Type[BaseBehaviour] = IsProfitableBehaviour

    @pytest.mark.parametrize(
        "credits, event, next_round",
        [
            (-1, Event.NOT_PROFITABLE, JobSelectionRound),
            (1, Event.PROFITABLE, PerformWorkRound),
        ],
    )
    def test_is_profitable(  # pylint: disable=redefined-builtin
        self, credits: bool, event: Event, next_round: Keep3rJobAbstractRound
    ) -> None:
        """Test is_profitable."""
        self.behaviour.act_wrapper()
        self.mock_read_keep3r_v1("credits", credits)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == next_round.auto_round_id()
        )


class TestAwaitTopUpBehaviour(Keep3rJobFSMBehaviourBaseCase):
    """Test case to test AwaitTopUpBehaviour."""

    behaviour_class: Type[BaseBehaviour] = AwaitTopUpBehaviour

    @pytest.mark.parametrize(
        "amount, event, next_round",
        [(1, Event.TOP_UP, PathSelectionRound)],
    )
    def test_top_up(
        self, amount: int, event: Event, next_round: Keep3rJobAbstractRound
    ) -> None:
        """Test top_up."""
        self.behaviour.act_wrapper()
        self.mock_ethereum_get_balance(amount=amount)
        self.behaviour.act_wrapper()
        self.mock_a2a_transaction()
        self._test_done_flag_set()
        self.end_round(done_event=event)
        assert (
            self.current_behaviour.matching_round.auto_round_id()
            == next_round.auto_round_id()
        )
