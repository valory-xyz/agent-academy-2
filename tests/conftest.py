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

"""Conftest module for Pytest."""

import inspect
import logging
import os
from pathlib import Path
from typing import Any, Generator, List, Tuple

import docker
import pytest
from aea_test_autonomy.configurations import KEY_PAIRS
from aea_test_autonomy.docker.base import launch_image
from aea_test_autonomy.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
)

from tests.helpers.docker.keep3r_net import Keep3rNetDockerImage


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = Path(CUR_PATH, "..").resolve().absolute()
THIRD_PARTY_CONTRACTS = ROOT_DIR / "third_party"

# Keep3rV1ForTest - Goerli
KEEP3R_V1_FOR_TEST = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"
KEEP3R_HELPER_FOR_TEST = "0x2720535578096f1dE6C8c9B5255F1Bda40e8067A"
KEEP3R_TEST_JOB = "0xd50345ca88e0B2cF9a6f5eD29C1F1f9d76A16C3c"

# Keep3rV1 - mainnet
KEEP3R_V1 = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
KEEP3R_HELPER = "0xb41772890c8b1564c5015a12c0dc6f18b0af955e"
KEEP3R_V1_LIBRARY = "0xfc38B6eBA9d47CBFc8C7B4FFfFd142B78996B6f1"


@pytest.fixture()
def hardhat_keep3r_addr() -> str:
    """Get the keep3r addr"""
    return DEFAULT_HARDHAT_ADDR


@pytest.fixture()
def hardhat_keep3r_port() -> int:
    """Get the keep3r port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture()
def hardhat_keep3r_key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for ganache."""
    return KEY_PAIRS


@pytest.fixture(scope="function")
def hardhat_keep3r_scope_function(
    hardhat_keep3r_addr: Any,
    hardhat_keep3r_port: Any,
    timeout: float = 3.0,
    max_attempts: int = 200,
) -> Generator:
    """Launch the Keep3r Test Network."""
    client = docker.from_env()
    end_point = f"{hardhat_keep3r_addr}:{hardhat_keep3r_port}"
    logging.info(f"Launching the Keep3r Network at {end_point}")
    image = Keep3rNetDockerImage(client, hardhat_keep3r_addr, hardhat_keep3r_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)
