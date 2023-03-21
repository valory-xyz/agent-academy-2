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

"""This module contains the class to connect to a keeper3 job Safe contract."""
from typing import Dict
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase

from packages.valory.contracts.keep3r_job.contract import (
    CONTRACT_ADDRESS,
    Keep3rJobContract,
)
from packages.valory.contracts.keep3r_job.tests import PACKAGE_DIR


CHAIN_ID = 1

GAS_PRICE = 20000000000
IS_WORKABLE = True

REWARD_MULTIPLIER = 975


class TestKeep3rJobContract(BaseContractTestCase):
    """Test Keep3rJobContract."""

    path_to_contract = PACKAGE_DIR
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

    def test_get_workable(self) -> None:
        """Test gets `workable` method."""
        # mock contract function
        mock_function = mock.MagicMock()
        mock_function.call.return_value = IS_WORKABLE
        # mock contract instance
        mock_instance = mock.MagicMock()
        mock_instance.functions.workable.return_value = mock_function

        with mock.patch.object(
            self.ledger_api, "get_contract_instance", return_value=mock_instance
        ):
            result = self.contract.get_workable(self.ledger_api, CONTRACT_ADDRESS)
        assert result.get("data", False) == IS_WORKABLE

    def test_reward_multiplier(self) -> None:
        """Test `reward_multiplier` method."""
        # mock contract function
        mock_function = mock.MagicMock()
        mock_function.call.return_value = REWARD_MULTIPLIER
        # mock contract instance
        mock_instance = mock.MagicMock()
        mock_instance.functions.rewardMultiplier.return_value = mock_function

        with mock.patch.object(
            self.ledger_api, "get_contract_instance", return_value=mock_instance
        ):
            result = self.contract.reward_multiplier(self.ledger_api, CONTRACT_ADDRESS)
        assert result.get("data") == REWARD_MULTIPLIER
