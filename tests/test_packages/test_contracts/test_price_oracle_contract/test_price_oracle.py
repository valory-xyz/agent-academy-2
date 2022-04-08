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

"""This module contains the class to connect to a price oracle contract."""
from pathlib import Path
from typing import Dict
from typing_extensions import Self
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase
from web3 import Web3

from packages.philippb.contracts.price_oracle.contract import (
    CONTRACT_ADDRESS,
    PriceOracleContract,
    PUBLIC_ID,
)

from tests.conftest import ROOT_DIR

K3PR_PRICE = Web3.toWei(0.14, "ether")

# This mocks the response of latestRoundData with the variables:
# round_id, answer, startedAt, updatedAt, answeredInRound
# We only care for'answer', giving the price denominated in ETH in Wei
LATEST_ROUND_DATA = [0,K3PR_PRICE, 0,0,0]

class TestPriceOracleContract(BaseContractTestCase):
    """Test PriceOracleContract."""

    path_to_contract = Path(
        ROOT_DIR, "packages", PUBLIC_ID.author, "contracts", PUBLIC_ID.name
    )
    ledger_identifier = "ethereum"
    contract: PriceOracleContract

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    
    def test_price_request(self):
        # mocking the function call
        mock_function = mock.MagicMock()
        mock_function.call.return_value = LATEST_ROUND_DATA
        # mocking the contract instance
        mock_instance = mock.MagicMock()
        mock_instance.functions.latestRoundData.return_value = mock_function

        with mock.patch.object(
            self.ledger_api, "get_contract_instance", return_value=mock_instance
        ):
            result = self.contract.get_kp3r_eth_price(self.ledger_api, CONTRACT_ADDRESS)

        assert result == LATEST_ROUND_DATA[1]