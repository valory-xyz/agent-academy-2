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
from typing import Any, Dict, cast

from aea_ledger_ethereum import EthereumApi, EthereumCrypto
from web3 import Web3
from web3.types import Wei

from autonomy.test_tools.base_test_classes.contracts import (
    BaseGanacheContractWithDependencyTest,
)
from autonomy.test_tools.docker.base import skip_docker_tests

from packages.valory.contracts.keep3r_v1.contract import (
    GOERLI_CONTRACT_ADDRESS,
    Keep3rV1Contract,
    PUBLIC_ID,
)
from packages.valory.contracts.keep3r_v1_library.contract import (
    PUBLIC_ID as LIBRARY_PUBLIC_ID,
)

from tests.conftest import ROOT_DIR
from tests.test_contracts.constants import DEFAULT_GAS


KEEPER_V1_HELPER = Web3.toChecksumAddress("0x2720535578096f1dE6C8c9B5255F1Bda40e8067A")
BASE_CONTRACT_PATH = Path(ROOT_DIR, "packages", PUBLIC_ID.author, "contracts")


class BaseKeep3rV1ContractTest(BaseGanacheContractWithDependencyTest):
    """Base class for the Keep3rV1 contract tests"""

    contract_address = GOERLI_CONTRACT_ADDRESS
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

        return dict(gas=DEFAULT_GAS, _kph=KEEPER_V1_HELPER)

    @property
    def contract(self) -> Keep3rV1Contract:  # type: ignore
        """Get the contract."""

        return cast(Keep3rV1Contract, super().contract)

    @property
    def _base_kw(self):
        """Keywords used in every transaction."""

        return dict(ledger_api=self.ledger_api, contract_address=self.contract_address)

    @property
    def funded_address(self) -> str:
        return self.key_pairs()[0][0]


@skip_docker_tests
class TestKeep3rV1Contract(BaseKeep3rV1ContractTest):
    """Test Keep3r V1 Contract"""

    def test_dependencies_deployed(self) -> None:
        """Test contract dependencies are successfully deployed"""

        assert self.dependency_info

    def test_contract_deployed(self) -> None:
        """Test contract is successfully deployed"""

        assert self.contract

    def test_get_jobs(self) -> None:
        """Test get_jobs"""

        assert self.contract.get_jobs(**self._base_kw) == []

    def test_is_keeper(self) -> None:
        """Test is_keeper"""

        address = self.funded_address
        assert not self.contract.is_keeper(**self._base_kw, address=address)

    def test_build_approve_tx(self) -> None:
        """Test build_approve_tx"""

        kw = dict(address=self.funded_address, amount=Wei(0))
        assert self.contract.build_approve_tx(**self._base_kw, **kw)

    def test_build_bond_tx(self) -> None:
        """Test build_bond_tx"""

        kw = dict(address=self.funded_address, amount=Wei(0))
        assert self.contract.build_bond_tx(**self._base_kw, **kw)

    def test_build_activate_tx(self) -> None:
        """Test build_activate_tx"""

        address = self.funded_address
        assert self.contract.build_activate_tx(**self._base_kw, address=address)

    def test_build_unbond_tx(self) -> None:
        """Test build_unbond_tx"""

        kw = dict(address=self.funded_address, amount=Wei(0))
        assert self.contract.build_unbond_tx(**self._base_kw, **kw)

    def test_build_withdraw_tx(self) -> None:
        """Test build_withdraw_tx"""

        address = self.funded_address
        assert self.contract.build_withdraw_tx(**self._base_kw, address=address)
