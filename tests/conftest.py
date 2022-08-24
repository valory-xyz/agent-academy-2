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
from typing import Any, Generator, List, Tuple, cast

import docker
import pytest

from autonomy.test_tools.configurations import KEY_PAIRS
from autonomy.test_tools.docker.base import launch_image, launch_many_containers
from autonomy.test_tools.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)
from autonomy.test_tools.docker.tendermint import (
    DEFAULT_ABCI_HOST,
    DEFAULT_ABCI_PORT,
    DEFAULT_TENDERMINT_PORT,
    FlaskTendermintDockerImage,
)

from tests.helpers.docker.keep3r_net import Keep3rNetDockerImage


def get_key(key_path: Path) -> str:
    """Returns key value from file.""" ""
    return key_path.read_bytes().strip().decode()


ANY_ADDRESS = "0.0.0.0"  # nosec

CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = Path(CUR_PATH, "..").resolve().absolute()

DATA_PATH = ROOT_DIR / "tests" / "data"
DEFAULT_AMOUNT = 1e21


@pytest.fixture()
def key_pairs() -> List[Tuple[str, str]]:
    """Get the default key paris for hardhat."""
    return KEY_PAIRS


@pytest.fixture(scope="session")
def tendermint_port() -> int:
    """Get the Tendermint port"""
    return DEFAULT_TENDERMINT_PORT


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
    max_attempts: int = 20,
) -> Generator:
    """Launch the HardHat node with Gnosis Safe contracts deployed."""
    client = docker.from_env()
    logging.info(f"Launching Hardhat at port {hardhat_port}")
    image = GnosisSafeNetDockerImage(client, hardhat_addr, hardhat_port)
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


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
