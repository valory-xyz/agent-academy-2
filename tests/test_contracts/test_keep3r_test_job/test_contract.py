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

from pathlib import Path
from typing import Any, Dict, cast

from aea_ledger_ethereum import EthereumApi, EthereumCrypto

from autonomy.test_tools.base_test_classes.contracts import BaseGanacheContractTest

from packages.valory.contracts.keep3r_test_job.contract import (
    GOERLI_CONTRACT_ADDRESS,
    Keep3rTestJobContract,
    PUBLIC_ID,
)
from packages.valory.contracts.keep3r_v1.contract import KEEP3R_V1_FOR_TEST

from tests.conftest import ROOT_DIR
from tests.test_contracts.constants import DEFAULT_GAS


BASE_CONTRACT_PATH = Path(ROOT_DIR, "packages", PUBLIC_ID.author, "contracts")


class BaseKeep3rTestJobContractTest(BaseGanacheContractTest):
    """Base Keep3r test job contract test"""

    contract_address = GOERLI_CONTRACT_ADDRESS
    contract_directory = BASE_CONTRACT_PATH / PUBLIC_ID.name

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


class TestKeep3rTestJobContract(BaseKeep3rTestJobContractTest):
    """Test Keep3rTestJobContract."""

    def test_workable(self) -> None:
        """Test workable, always true for test contract"""

        assert self.contract.workable(self.ledger_api, self.contract_address)

    def test_build_work_tx(self) -> None:
        """Test build work transaction"""

        kw = dict(address=self.key_pairs()[0][0])
        assert self.contract.build_work_tx(self.ledger_api, self.contract_address, **kw)
