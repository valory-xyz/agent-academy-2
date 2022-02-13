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
from typing import Any, Generator, List, Tuple

import docker
import pytest

from tests.helpers.constants import KEY_PAIRS
from tests.helpers.constants import ROOT_DIR as _ROOT_DIR
from tests.helpers.docker.base import launch_image
from tests.helpers.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
    GnosisSafeNetDockerImage,
)


ROOT_DIR = _ROOT_DIR


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
