from pathlib import Path
from typing import Dict
from unittest import mock

from aea.test_tools.test_contract import BaseContractTestCase

from packages.gabrielfu.contracts.keep3r_job.contract import (
    PUBLIC_ID,
    CONTRACT_ADDRESS,
    Keep3rJobContract
)

from tests.conftest import ROOT_DIR


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
                result = self.contract.get_gas_price(self.ledger_api,)
        assert result == 20000000000