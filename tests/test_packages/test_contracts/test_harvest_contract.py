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
from pathlib import Path
from typing import Dict
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase

from packages.philippb.contracts.keep3r_harvest_job.contract import (
    CONTRACT_ADDRESS as HARVEST_CONTRACT_ADDRESS,
    Keep3rHarvestJobContract,
    PUBLIC_ID as HARVEST_PUBLIC_ID
)

from tests.conftest import ROOT_DIR


IS_WORKABLE = True

REWARD_MULTIPLIER = 975

class TestKeep3rHarvestJobContract(BaseContractTestCase):
    """Test Keep3r Harvest Job Contract."""

    path_to_contract = Path(
        ROOT_DIR, "packages", HARVEST_PUBLIC_ID.author, "contracts", HARVEST_PUBLIC_ID.name
    )
    ledger_identifier = "ethereum"
    contract: Keep3rHarvestJobContract

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        contract_address = HARVEST_CONTRACT_ADDRESS
        return contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    def test_get_reward_multiplier(self) -> None:
        # mock contract function
        mock_function = mock.MagicMock()
        mock_function.call.return_value = REWARD_MULTIPLIER
        # mock contract instance
        mock_instance = mock.MagicMock()
        mock_instance.functions.get_reward_multiplier.return_value = mock_function

        with mock.patch.object(
            self.ledger_api, "get_contract_instance", return_value=mock_instance
        ):
            result = self.contract.get_reward_multiplier(self.ledger_api, HARVEST_CONTRACT_ADDRESS)
        assert result == REWARD_MULTIPLIER