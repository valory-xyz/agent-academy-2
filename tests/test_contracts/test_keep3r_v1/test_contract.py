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

from autonomy.test_tools.base_test_classes.contracts import (
    BaseGanacheContractWithDependencyTest,
)
from autonomy.test_tools.docker.base import skip_docker_tests

from packages.valory.contracts.keep3r_v1.contract import Keep3rV1Contract, PUBLIC_ID
from packages.valory.contracts.keep3r_v1_library.contract import (
    PUBLIC_ID as LIBRARY_PUBLIC_ID,
)

from tests.conftest import KEEP3R_HELPER_FOR_TEST, KEEP3R_V1_FOR_TEST, ROOT_DIR
from tests.test_contracts.constants import DEFAULT_GAS, ONE_ETH


BASE_CONTRACT_PATH = Path(ROOT_DIR, "packages", PUBLIC_ID.author, "contracts")


class BaseKeep3rV1ContractTest(BaseGanacheContractWithDependencyTest):
    """Base class for the Keep3rV1 contract tests"""

    contract_address = KEEP3R_V1_FOR_TEST
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

        return dict(gas=DEFAULT_GAS, _kph=KEEP3R_HELPER_FOR_TEST)

    @property
    def contract(self) -> Keep3rV1Contract:  # type: ignore
        """Get the contract."""

        return cast(Keep3rV1Contract, super().contract)

    @property
    def alice_address(self) -> str:
        """Alice's wallet; funded with 1000 ETH"""

        return self.key_pairs()[0][0]

    @property
    def bob_address(self) -> str:
        """Bob's wallet; empty"""

        return "0x1B621c19C3E868A4DF2E1858b08cedA8633927EA"

    @property
    def base_kw(self) -> Dict[str, str]:
        """Keyword arguments expected by every method call"""

        return dict(ledger_api=self.ledger_api, contract_address=self.contract_address)


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

        assert self.contract.get_jobs(self.ledger_api, self.contract_address) == []

    def test_is_keeper(self) -> None:
        """Test is_keeper"""

        kw = dict(address=self.alice_address)
        assert self.contract.is_keeper(**self.base_kw, **kw) is False

    def test_build_approve_tx(self) -> None:
        """Test get_jobs"""

        kw = dict(address=self.alice_address, spender=self.bob_address, amount=ONE_ETH)
        raw_tx = self.contract.build_approve_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0x095ea7b30000000000000000000000001b621c19c3e868a4df2e1858b08ceda8633927ea0000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_allowance(self) -> None:
        """Test allowance"""

        kw = dict(account=self.alice_address, spender=self.bob_address)
        assert self.contract.allowance(**self.base_kw, **kw) == 0

    def test_build_bond_tx(self) -> None:
        """Test build_bond_tx"""

        kw = dict(address=self.bob_address, amount=ONE_ETH)
        raw_tx = self.contract.build_bond_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0xa515366a000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f05120000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_build_activate_tx(self) -> None:
        """Test build_activate_tx"""

        kw = dict(address=self.alice_address)
        raw_tx = self.contract.build_activate_tx(**self.base_kw, **kw)
        expected = (
            "0x1c5a9d9c000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f0512"
        )
        assert raw_tx["data"] == expected

    def test_build_unbond_tx(self) -> None:
        """Test build_unbond_tx"""

        kw = dict(address=self.bob_address, amount=ONE_ETH)
        raw_tx = self.contract.build_unbond_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0xa5d059ca000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f05120000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_build_withdraw_tx(self) -> None:
        """Test build_withdraw_tx"""

        kw = dict(address=self.alice_address)
        raw_tx = self.contract.build_withdraw_tx(**self.base_kw, **kw)
        expected = (
            "0x51cff8d9000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f0512"
        )
        assert raw_tx["data"] == expected
