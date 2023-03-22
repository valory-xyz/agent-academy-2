# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
# pylint: disable=import-error

"""Tests for the keep3r contract."""

from pathlib import Path
from typing import Any, Dict, Generator, cast

import docker
import pytest
from aea.test_tools.test_contract import BaseContractTestCase
from aea_ledger_ethereum import EthereumCrypto
from aea_test_autonomy.docker.base import launch_image, skip_docker_tests
from aea_test_autonomy.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
    GanacheForkDockerImage,
)
from aea_test_autonomy.fixture_helpers import (  # noqa
    ganache_addr,
    ganache_configuration,
    ganache_port,
)

from packages.valory.contracts.phuture_harvesting_job.contract import (
    PhutureHarvestingJobContract,
)


ENDPOINT_GANACHE_URI = f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}"
RECEIPT_TIMEOUT = 30
PHUTURE_HARVESTING_JOB_ADDRESS = "0xEC771dc7Bd0aA67a10b1aF124B9b9a0DC4aF5F9B"


@skip_docker_tests
class TestPhutureHarvestingJob(BaseContractTestCase):
    """Test PhutureHarvestingJob contract."""

    contract_address = PHUTURE_HARVESTING_JOB_ADDRESS
    path_to_contract = Path(__file__).parent
    ledger_identifier = EthereumCrypto.identifier
    contract: PhutureHarvestingJobContract

    # ganache fork configuration
    NETWORK_TO_FORK = "mainnet"
    BLOCK_TO_FORK_FROM = 16712444

    @property
    def base_kw(self) -> Dict[str, Any]:
        """Keyword arguments expected by every method call"""
        return dict(ledger_api=self.ledger_api, contract_address=self.contract_address)

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        return cls.contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    def test_become_keeper(self) -> None:
        """Test become keeper"""
        # the contract should be workable at the block that we are forking on
        contract = cast(PhutureHarvestingJobContract, self.contract)
        workable = contract.workable(self.ledger_api, self.contract_address)
        assert workable.get("data", False)

        # a work tx should be prepared succesfully
        work_tx = contract.build_work_tx(self.ledger_api, self.contract_address)
        assert work_tx.get("data", False)

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
