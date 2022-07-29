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
import logging
from pathlib import Path
from typing import Any, Generator, List, Tuple, cast

import docker
import pytest

from tests.helpers.constants import GANACHE_KEY_PAIRS, KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image, launch_many_containers
from tests.helpers.docker.ganache import DEFAULT_GANACHE_ADDR, DEFAULT_GANACHE_PORT
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from tests.helpers.docker.tendermint import (
    DEFAULT_ABCI_HOST,
    DEFAULT_ABCI_PORT,
    DEFAULT_TENDERMINT_PORT,
    FlaskTendermintDockerImage,
    TendermintDockerImage,
)


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


ANY_ADDRESS = "0.0.0.0"  # nosec

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


@pytest.fixture(scope="session")
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


@pytest.fixture(scope="class")
def tendermint(
    tendermint_port: Any,
    abci_host: str = DEFAULT_ABCI_HOST,
    abci_port: int = DEFAULT_ABCI_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator:
    """Launch the Ganache image."""
    client = docker.from_env()
    logging.info(f"Launching Tendermint at port {tendermint_port}")
    image = TendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture
def nb_nodes(request: Any) -> int:
    """Get a parametrized number of nodes."""
    return request.param


@pytest.fixture
def flask_tendermint(
    tendermint_port: Any,
    nb_nodes: int,
    abci_host: str = DEFAULT_ABCI_HOST,
    abci_port: int = DEFAULT_ABCI_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
) -> Generator[FlaskTendermintDockerImage, None, None]:
    """Launch the Flask server with Tendermint container."""
    client = docker.from_env()
    logging.info(
        f"Launching Tendermint nodes at ports {[tendermint_port + i * 10 for i in range(nb_nodes)]}"
    )
    image = FlaskTendermintDockerImage(client, abci_host, abci_port, tendermint_port)
    yield from cast(
        Generator[FlaskTendermintDockerImage, None, None],
        launch_many_containers(image, nb_nodes, timeout, max_attempts),
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
