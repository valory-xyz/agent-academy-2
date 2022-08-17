# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Tests for the keep3r v1 contract."""

from pathlib import Path
from typing import Dict, Any, cast

from autonomy.test_tools.base_test_classes.contracts import (
    BaseGanacheContractWithDependencyTest,
)
from web3 import Web3
from aea_ledger_ethereum import EthereumCrypto, EthereumApi

from autonomy.test_tools.docker.base import skip_docker_tests

from packages.valory.contracts.keep3r_v1_library.contract import PUBLIC_ID as LIBRARY_PUBLIC_ID
from packages.valory.contracts.keep3r_v1.contract import (
    PUBLIC_ID,
    Keep3rV1Contract,
)

from tests.conftest import ROOT_DIR


DEFAULT_GAS = 10000000
DEFAULT_MAX_FEE_PER_GAS = 10 ** 10
DEFAULT_MAX_PRIORITY_FEE_PER_GAS = 10 ** 10
DEPLOYER = Web3.toChecksumAddress("0x1fdf6a150ffc90dcc61c05d9b641a242fcc37823")

BASE_CONTRACT_PATH = Path(ROOT_DIR, "packages", PUBLIC_ID.author, "contracts")


class BaseKeep3rV1ContractTest(BaseGanacheContractWithDependencyTest):
    """Base class for the Keep3rV1 contract tests"""

    contract: Keep3rV1Contract
    contract_address = Keep3rV1Contract.address
    contract_directory = BASE_CONTRACT_PATH / PUBLIC_ID.name

    ledger_api: EthereumApi
    ledger_identifier = EthereumCrypto.identifier

    dependencies = [
                       (
                           LIBRARY_PUBLIC_ID.name,
                           Path(BASE_CONTRACT_PATH / LIBRARY_PUBLIC_ID.name),
                           dict(gas=DEFAULT_GAS),
                       ),
                    ]

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""

        return dict(gas=DEFAULT_GAS, _kph=DEPLOYER)

    @property
    def contract(self) -> Keep3rV1Contract:
        """Get the contract."""
        return cast(Keep3rV1Contract, super().contract)


@skip_docker_tests
class TestKeep3rV1Contract(BaseKeep3rV1ContractTest):
    """Test Keep3r V1 Contract"""

    def test_dependencies_deployed(self):
        """Test contract dependencies are successfully deployed"""

        assert self.dependency_info

    def test_contract_deployed(self) -> None:
        """Test contract is successfully deployed"""

        assert self.contract
