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
import json
import logging
from pathlib import Path
from typing import Any, Generator, List, Tuple

import docker
import pytest
from web3 import Web3

from tests.helpers.constants import ARTBLOCKS_ADDRESS, GANACHE_KEY_PAIRS, KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.constants import TARGET_PROJECT_ID
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheForkDockerImage,
)
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


ROOT_DIR = _ROOT_DIR

DATA_PATH = _ROOT_DIR / "tests" / "data"
DEFAULT_AMOUNT = 1000000000000000000000

ETHEREUM_KEY_DEPLOYER = DATA_PATH / "ethereum_key_deployer.txt"
ETHEREUM_KEY_PATH_1 = DATA_PATH / "ethereum_key_1.txt"
ETHEREUM_KEY_PATH_2 = DATA_PATH / "ethereum_key_2.txt"
ETHEREUM_KEY_PATH_3 = DATA_PATH / "ethereum_key_3.txt"
ETHEREUM_KEY_PATH_4 = DATA_PATH / "ethereum_key_4.txt"
GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (get_key(ETHEREUM_KEY_DEPLOYER), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_1), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_2), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_3), DEFAULT_AMOUNT),
        (get_key(ETHEREUM_KEY_PATH_4), DEFAULT_AMOUNT),
    ],
)


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.fixture()
def hardhat_addr() -> str:
    """Get the hardhat addr"""
    return DEFAULT_HARDHAT_ADDR


@pytest.fixture()
def hardhat_port() -> int:
    """Get the hardhat port"""
    return DEFAULT_HARDHAT_PORT


@pytest.fixture(scope="function")
def gnosis_safe_hardhat_scope_function(
    hardhat_addr: Any,
    hardhat_port: Any,
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture()
def ganache_key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for ganache."""
    return GANACHE_KEY_PAIRS


@pytest.fixture()
def ganache_addr() -> str:
    """Get the ganache addr"""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture()
def ganache_port() -> int:
    """Get the ganache port"""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="function")
def ganache_fork_scope_function(
    ganache_addr: Any,
    ganache_port: Any,
    timeout: float = 3.0,
    max_attempts: int = 40,
) -> Generator:
    """Launch the Ganache Fork. This fixture is scoped to a function which means it will destroyed at the end of the test."""
    client = docker.from_env()
    logging.info(f"Launching Ganache at port {ganache_port}")
    image = GanacheForkDockerImage(client, ganache_addr, ganache_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture()
def ganache_fork_engine_warmer_function(
    ganache_fork_scope_function: Any,
    ganache_addr: Any,
    ganache_port: Any,
    timeout: float = 60.0,
) -> None:
    """The ganache fork is very slow on the first try. This function is used to go through the same steps as the agent would do later."""

    path_to_artblocks = Path(
        _ROOT_DIR,
        "packages",
        "valory",
        "contracts",
        "artblocks",
        "build",
        "artblocks.json",
    )

    with open(path_to_artblocks) as f:
        artblocks_abi = json.load(f)["abi"]

    w3 = Web3(
        Web3.HTTPProvider(
            f"{ganache_addr}:{ganache_port}", request_kwargs={"timeout": timeout}
        )
    )

    artblocks = w3.eth.contract(address=ARTBLOCKS_ADDRESS, abi=artblocks_abi)  # type: ignore
    project_info = artblocks.caller.projectTokenInfo(TARGET_PROJECT_ID)
    if project_info[4]:
        script_info = artblocks.caller.projectScriptInfo(TARGET_PROJECT_ID)
        artblocks.caller.projectScriptByIndex(TARGET_PROJECT_ID, script_info[1] - 1)
    artblocks.caller.projectDetails(TARGET_PROJECT_ID)
