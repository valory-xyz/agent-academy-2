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

"""This module contains the tests for the Keeper3 TestJob contract."""

from typing import Any, Dict, cast

from aea_ledger_ethereum import EthereumApi, EthereumCrypto
from aea_test_autonomy.base_test_classes.contracts import BaseGanacheContractTest
from aea_test_autonomy.docker.base import skip_docker_tests

from packages.valory.contracts.keep3r_test_job.contract import Keep3rTestJobContract
from packages.valory.contracts.keep3r_test_job.tests import PACKAGE_DIR


# Keep3rV1ForTest - Goerli
KEEP3R_V1_FOR_TEST = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"
KEEP3R_HELPER_FOR_TEST = "0x2720535578096f1dE6C8c9B5255F1Bda40e8067A"
KEEP3R_TEST_JOB = "0xd50345ca88e0B2cF9a6f5eD29C1F1f9d76A16C3c"

DEFAULT_GAS = 10 ** 7


class BaseKeep3rTestJobContractTest(BaseGanacheContractTest):
    """Base Keep3r test job contract test"""

    contract_address = KEEP3R_TEST_JOB
    contract_directory = PACKAGE_DIR

    ledger_api: EthereumApi
    ledger_identifier = EthereumCrypto.identifier

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""

        return dict(gas=DEFAULT_GAS, _keep3r=KEEP3R_V1_FOR_TEST)

    @property
    def contract(self) -> Keep3rTestJobContract:  # type: ignore
        """Get the contract."""

        return cast(Keep3rTestJobContract, super().contract)


@skip_docker_tests
class TestKeep3rTestJobContract(BaseKeep3rTestJobContractTest):
    """Test Keep3rTestJobContract."""

    def test_workable(self) -> None:
        """Test workable, always true for test contract"""

        assert self.contract.workable(self.ledger_api, self.contract_address)

    def test_build_work_tx(self) -> None:
        """Test build work transaction"""

        kw = dict(address=self.key_pairs()[0][0])
        assert self.contract.build_work_tx(self.ledger_api, self.contract_address, **kw)
