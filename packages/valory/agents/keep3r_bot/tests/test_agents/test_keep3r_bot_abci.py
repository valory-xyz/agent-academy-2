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
# pylint: disable=import-error,too-few-public-methods,no-self-use
# flake8: noqa: B028

"""End-to-end tests for the valory/keep3r_abci skill."""
import json
import threading
from pathlib import Path

import pytest
from aea.configurations.data_types import PublicId
from aea_test_autonomy.base_test_classes.agents import BaseTestEnd2End
from web3 import HTTPProvider, Web3
from web3.providers import BaseProvider
from web3.types import RPCEndpoint

from packages.valory.agents.keep3r_bot.tests.conftest import (
    KEEP3R_V1_FOR_TEST,
    KEEP3R_V1_TEST_JOB_ADDRESS,
    KEEP3R_V2_TEST_JOB_ADDRESS,
    SAFE_CONTRACT_ADDRESS,
    UseGanacheFork,
    WETH_ADDRESS,
    get_ipfs_hash_from_contract_id,
)
from packages.valory.skills.keep3r_job_abci.rounds import (
    ActivationRound,
    ApproveBondRound,
    BondingRound,
    GetJobsRound,
    IsProfitableRound,
    IsWorkableRound,
    PathSelectionRound,
    PerformWorkRound,
    WaitingRound,
)
from packages.valory.skills.registration_abci.rounds import RegistrationStartupRound


# check log messages of the happy path
CHECK_STRINGS = (
    f"Entered in the '{RegistrationStartupRound.auto_round_id()}' round for period 0",
    f"'{RegistrationStartupRound.auto_round_id()}' round is done with event: Event.DONE",
    f"Entered in the '{PathSelectionRound.auto_round_id()}'",
    f"'{PathSelectionRound.auto_round_id()}' round is done with event: Event.APPROVE_BOND",
    f"'{PathSelectionRound.auto_round_id()}' round is done with event: Event.NOT_BONDED",
    f"'{PathSelectionRound.auto_round_id()}' round is done with event: Event.NOT_ACTIVATED",
    f"'{PathSelectionRound.auto_round_id()}' round is done with event: Event.HEALTHY",
    f"Entered in the '{ApproveBondRound.auto_round_id()}' round",
    f"'{ApproveBondRound.auto_round_id()}' round is done with event: Event.APPROVE_BOND",
    f"Entered in the '{BondingRound.auto_round_id()}' round",
    f"'{BondingRound.auto_round_id()}' round is done with event: Event.BONDING_TX",
    f"Entered in the '{WaitingRound.auto_round_id()}' round",
    f"'{WaitingRound.auto_round_id()}' round is done with event: Event.DONE",
    f"Entered in the '{ActivationRound.auto_round_id()}' round",
    f"'{ActivationRound.auto_round_id()}' round is done with event: Event.ACTIVATION_TX",
    f"Entered in the '{GetJobsRound.auto_round_id()}' round",
    f"'{GetJobsRound.auto_round_id()}' round is done with event: Event.DONE",
    f"Entered in the '{IsWorkableRound.auto_round_id()}' round",
    f"'{IsWorkableRound.auto_round_id()}' round is done with event: Event.WORKABLE",
    f"Entered in the '{IsProfitableRound.auto_round_id()}' round",
    f"'{IsProfitableRound.auto_round_id()}' round is done with event: Event.PROFITABLE",
    f"Entered in the '{PerformWorkRound.auto_round_id()}' round",
    f"'{PerformWorkRound.auto_round_id()}' round is done with event: Event.WORK_TX",
)

TERMINATION_TIMEOUT = 120

PACKAGES_PATH = Path(__file__).parents[5]
TARGET_SKILL = "valory/keep3r_abci:0.1.0"
TARGET_AGENT = "valory/keep3r_bot:0.1.0"
TARGET_CONTRACT_PACKAGE = "contract/valory/keep3r_test_job/0.1.0"
TARGET_CONTRACT_HASH = get_ipfs_hash_from_contract_id(
    PACKAGES_PATH / "packages.json", TARGET_CONTRACT_PACKAGE
)


class BaseKeep3rABCITest(BaseTestEnd2End, UseGanacheFork):
    """BaseKeep3rABCITest"""

    agent_package = TARGET_AGENT
    skill_package = TARGET_SKILL
    wait_to_finish = 360
    ROUND_TIMEOUT_SECONDS = 60.0
    strict_check_strings = CHECK_STRINGS
    use_benchmarks = True
    network_endpoint = "http://127.0.0.1:8545"
    package_registry_src = package_registry_src_rel = PACKAGES_PATH
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(skill_package).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.keep3r_v1_contract_address",
            "value": KEEP3R_V1_FOR_TEST,
        },
        {
            "dotted_path": f"{__args_prefix}.job_contract_addresses",
            "value": json.dumps([KEEP3R_V1_TEST_JOB_ADDRESS]),
            "type_": "list",
        },
        {
            "dotted_path": f"{__args_prefix}.setup.safe_contract_address",
            "value": json.dumps([SAFE_CONTRACT_ADDRESS]),
            "type_": "list",
        },
        {
            "dotted_path": f"{__args_prefix}.bonding_asset",
            "value": WETH_ADDRESS,
        },
        {
            "dotted_path": f"{__args_prefix}.supported_jobs_to_package_hash",
            "value": json.dumps([[KEEP3R_V2_TEST_JOB_ADDRESS, TARGET_CONTRACT_HASH]]),
            "type_": "list",
        },
    ]

    def test_run(self, nb_nodes: int) -> None:
        """Run the test."""
        self.prepare_and_launch(nb_nodes)
        self.health_check(
            max_retries=self.HEALTH_CHECK_MAX_RETRIES,
            sleep_interval=self.HEALTH_CHECK_SLEEP_INTERVAL,
        )
        self.fast_forward_on_period_end()
        self.check_aea_messages()
        self.terminate_agents(timeout=TERMINATION_TIMEOUT)

    def fast_forward_on_period_end(self) -> None:
        """Mines a block and fast forwards time by 3 days once a period is over."""
        web3_provider = Web3(provider=HTTPProvider(self.network_endpoint)).provider
        thread = threading.Thread(
            target=self._check_logs_and_fast_forward, args=(web3_provider,)
        )
        thread.start()

    def _check_logs_and_fast_forward(self, web3_provider: BaseProvider) -> None:
        """Checks the logs and fast forwards time."""
        prev_count, num_changes = 0, 0
        num_required_changes = 3
        trigger = "Period end."
        while True:
            for output in self.stdout.values():
                count = output.count(trigger)
                if count > prev_count:
                    three_days = 3 * 24 * 60 * 60
                    self._fast_forward_time(web3_provider, three_days)
                    self._mine_block(web3_provider)
                    prev_count = count
                    num_changes += 1
                if num_changes == num_required_changes:
                    return

    def _mine_block(self, web3_provider: BaseProvider) -> None:
        """Mines a block."""
        endpoint = RPCEndpoint("evm_mine")
        web3_provider.make_request(endpoint, [])

    def _fast_forward_time(self, web3_provider: BaseProvider, time: int) -> None:
        """Fast forwards time by the given amount of seconds."""
        endpoint = RPCEndpoint("evm_increaseTime")
        web3_provider.make_request(endpoint, [time])


@pytest.mark.skip
@pytest.mark.parametrize("nb_nodes", (1,))
class TestKeep3rABCISingleAgentV2(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with only one agent."""


@pytest.mark.skip
@pytest.mark.parametrize("nb_nodes", (2,))
class TestKeep3rABCITwoAgentsV2(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with two agents."""


@pytest.mark.skip(reason="Flashbots cannot be used on the local net")
@pytest.mark.parametrize("nb_nodes", (4,))
class TestKeep3rABCIFourAgentsV2(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with four agents."""

    BLOCK_TO_FORK_FROM = 8420525


@pytest.mark.skip(reason="Flashbots cannot be used on the local net")
@pytest.mark.parametrize("nb_nodes", (4,))
class TestKeep3rABCIFourAgentsV1(BaseKeep3rABCITest):
    """Test that the ABCI keep3r_abci skill with four agents."""

    skill_package = TARGET_SKILL
    __args_prefix = f"vendor.valory.skills.{PublicId.from_str(TARGET_SKILL).name}.models.params.args"
    extra_configs = [
        {
            "dotted_path": f"{__args_prefix}.keep3r_v1_contract_address",
            "value": KEEP3R_V1_FOR_TEST,
        },
        {
            "dotted_path": f"{__args_prefix}.job_contract_addresses",
            "value": json.dumps([KEEP3R_V1_TEST_JOB_ADDRESS]),
            "type_": "list",
        },
        {
            "dotted_path": f"{__args_prefix}.setup.safe_contract_address",
            "value": json.dumps([SAFE_CONTRACT_ADDRESS]),
            "type_": "list",
        },
        {
            "dotted_path": f"{__args_prefix}.bonding_asset",
            "value": WETH_ADDRESS,
        },
        {
            "dotted_path": f"{__args_prefix}.use_v2",
            "value": "false",
            "type_": "bool",
        },
        {
            "dotted_path": f"{__args_prefix}.supported_jobs_to_package_hash",
            "value": json.dumps([[KEEP3R_V1_TEST_JOB_ADDRESS, TARGET_CONTRACT_HASH]]),
            "type_": "list",
        },
    ]
