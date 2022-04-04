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

"""Test the contract.py module of the contract."""
from pathlib import Path
from typing import Dict
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase

from packages.gabrielfu.contracts.keep3r_job.contract import (
    Keep3rJobContract,
    PUBLIC_ID,
)

from tests.conftest import ROOT_DIR


CONTRACT_ADDRESS = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
NONCE = 0
CHAIN_ID = 1

GAS_PRICE = 20000000000


class TestKeep3rJobContract(BaseContractTestCase):
    """Test TestUniswapV2ERC20Contract."""

    path_to_contract = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )
    ledger_identifier = "ethereum"
    contract: Keep3rJobContract

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    def test_get_gas_price(self) -> None:
        """Test gets gas price."""
        with mock.patch.object(
            self.ledger_api.api.eth, "generate_gas_price", return_value=GAS_PRICE
        ):
            with mock.patch.object(
                self.ledger_api.api.manager, "request_blocking", return_value=CHAIN_ID
            ):
                result = self.contract.get_gas_price(
                    self.ledger_api,
                )
        assert result == 20000000000
