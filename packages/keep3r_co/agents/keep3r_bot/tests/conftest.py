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
# pylint: disable=import-error,unused-import
# flake8: noqa

"""Conftest module for Pytest."""
import json
from pathlib import Path
from typing import Dict, Generator, List, Tuple

import docker
import pytest
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.docker.ganache import GanacheForkDockerImage
from aea_test_autonomy.fixture_helpers import (  # noqa
    abci_host,
    abci_port,
    flask_tendermint,
    ganache_addr,
    ganache_configuration,
    ganache_port,
    ipfs_daemon,
    tendermint_port,
)

from packages.keep3r_co.agents.keep3r_bot.tests.helpers.constants import (
    GANACHE_KEY_PAIRS,
)


# Keep3rV1ForTest - Goerli
KEEP3R_V1_FOR_TEST = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"
KEEP3R_HELPER_FOR_TEST = "0x2720535578096f1dE6C8c9B5255F1Bda40e8067A"
KEEP3R_V1_TEST_JOB_ADDRESS = "0x7e745448d05c56ebf0fD1E74E87d102fF4A6Fd99"

# Keep3rV2ForTest - Goerli
KEEP3R_V2_FOR_TEST = "0x85063437C02Ba7F4f82F898859e4992380DEd3bb"
KEEP3R_V2_TEST_JOB_ADDRESS = "0x90E6E53Ded5A1e272941249390CcA5BBB70cF2a4"


SAFE_CONTRACT_ADDRESS = "0x3d5AF15895fb88fd4E708282d752E0346E7a359F"
WETH_ADDRESS = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"

# Keep3rV1 - mainnet
KEEP3R_V1 = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
KEEP3R_HELPER = "0xb41772890c8b1564c5015a12c0dc6f18b0af955e"
KEEP3R_V1_LIBRARY = "0xfc38B6eBA9d47CBFc8C7B4FFfFd142B78996B6f1"


def get_ipfs_hash_from_contract_id(packages_json_path: Path, contract_id: str) -> str:
    """Get the hash from the contract id."""
    with open(packages_json_path, "r", encoding="utf-8") as f:
        packages = json.load(f)["dev"]
    assert (
        contract_id in packages
    ), f"Contract id {contract_id} not found in packages.json"
    return packages[contract_id]


@pytest.mark.integration
class UseGanacheFork:  # pylint: disable=too-few-public-methods
    """Inherit from this class to use Ganache."""

    NETWORK_TO_FORK = "goerli"
    BLOCK_TO_FORK_FROM = 8378809

    key_pairs: List[Tuple[str, str]] = GANACHE_KEY_PAIRS

    @classmethod
    @pytest.fixture(autouse=True, scope="class")
    def _start_ganache(
        cls,
        ganache_configuration: Dict,  # pylint: disable=redefined-outer-name
        ganache_addr: str,  # pylint: disable=redefined-outer-name
        ganache_port: int,  # pylint: disable=redefined-outer-name
        timeout: float = 2.0,
        max_attempts: int = 10,
    ) -> Generator:
        """Start Ganache instance."""
        client = docker.from_env()
        GanacheForkDockerImage.NETWORK = cls.NETWORK_TO_FORK
        GanacheForkDockerImage.BLOCK_NUMBER = cls.BLOCK_TO_FORK_FROM
        image = GanacheForkDockerImage(
            client, ganache_addr, ganache_port, config=ganache_configuration
        )
        yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="session")
def ipfs_domain() -> str:
    """Get the ipfs domain"""
    default_domain = "/dns/registry.autonolas.tech/tcp/443/https"
    return default_domain
