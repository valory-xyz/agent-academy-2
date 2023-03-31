# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
# pylint: disable=import-error

"""Tests for the keep3r contract."""

import logging
import os
import tempfile
import time
from typing import Any, Dict, cast

from aea.common import JSONLike
from aea.configurations.base import ContractConfig
from aea.configurations.data_types import ComponentType
from aea.configurations.loader import load_component_configuration
from aea.contracts import Contract, contract_registry
from aea.crypto.registries import crypto_registry
from aea.test_tools.test_contract import BaseContractTestCase
from aea.test_tools.utils import wait_for_condition
from aea_ledger_ethereum import EthereumCrypto
from aea_test_autonomy.docker.base import skip_docker_tests
from aea_test_autonomy.docker.ganache import DEFAULT_GANACHE_ADDR, DEFAULT_GANACHE_PORT
from web3 import HTTPProvider, Web3
from web3.types import Nonce, RPCEndpoint

from packages.valory.agents.keep3r_bot.tests.conftest import (
    KEEP3R_V2_FOR_TEST,
    UseGanacheFork,
)
from packages.valory.agents.keep3r_bot.tests.helpers.constants import (
    DEFAULT_GAS,
    GANACHE_KEY_PAIRS,
    HALF_A_SECOND,
    SECONDS_PER_DAY,
)
from packages.valory.contracts.keep3r_v2 import (
    PACKAGE_DIR as KEEPER_FOR_TESTNET_DIR,
)
from packages.valory.contracts.keep3r_v2.contract import (
    KeeperV2,
)
from packages.valory.contracts.keep3r_v1 import PACKAGE_DIR as KEEP3R_V1_DIR
from packages.valory.contracts.keep3r_v1.contract import Keep3rV1Contract


ENDPOINT_GANACHE_URI = f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}"
RECEIPT_TIMEOUT = 30


@skip_docker_tests
class TestKeep3rV1ContractWithTestJob(BaseContractTestCase, UseGanacheFork):
    """Test Keep3r V1 Contract in conjunction with the TestJob contract."""

    contract_address = KEEP3R_V2_FOR_TEST
    path_to_contract = KEEPER_FOR_TESTNET_DIR
    ledger_identifier = EthereumCrypto.identifier
    contract: KeeperV2
    keep3rv1_contract: Keep3rV1Contract
    keep3rv1_path = KEEP3R_V1_DIR
    BLOCK_TO_FORK_FROM = 8378981

    private_key_path: str
    dummy_erc20_token = "0x22404B0e2a7067068AcdaDd8f9D586F834cCe2c5"  # nosec
    ganache_provider = Web3(provider=HTTPProvider(ENDPOINT_GANACHE_URI)).provider

    @classmethod
    def mine_block(cls) -> None:
        """Force a block to be mined. Takes no parameters. Mines a block independent of whether or not mining is started or stopped."""

        endpoint = RPCEndpoint("evm_mine")
        cls.ganache_provider.make_request(endpoint, [])
        block_number = cls.ledger_api.api.eth.get_block_number()
        logging.info(f"Block {block_number} forcefully mined")

    @classmethod
    def time_jump(cls, seconds: int) -> None:
        """Jump forward in time. Takes one parameter, which is the amount of time to increase in seconds."""

        endpoint = RPCEndpoint("evm_increaseTime")
        response = cls.ganache_provider.make_request(endpoint, [seconds])
        logging.info(f"Time jumped to {response['result']} seconds")

    @property
    def base_kw(self) -> Dict[str, Any]:
        """Keyword arguments expected by every method call"""

        return dict(ledger_api=self.ledger_api, contract_address=self.contract_address)

    @classmethod
    def finish_contract_deployment(cls) -> str:
        """Finish the contract deployment."""
        return cls.contract_address

    @classmethod
    def _deploy_contract(cls, contract, ledger_api, deployer_crypto, gas) -> Dict:  # type: ignore
        """Deploy contract."""
        return {}

    @classmethod
    def setup_class(cls) -> None:
        """Setup the test."""
        super().setup_class()
        _, pk = GANACHE_KEY_PAIRS[0]
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, "w") as tmp:
            tmp.write(pk)
        cls.private_key_path = path
        cls._setup_keep3rv1()

    @classmethod
    def _setup_keep3rv1(cls) -> None:
        """Setup Keep3r V1 contract."""
        configuration = cast(
            ContractConfig,
            load_component_configuration(ComponentType.CONTRACT, cls.keep3rv1_path),
        )
        configuration._directory = cls.keep3rv1_path  # pylint: disable=protected-access
        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)  # pragma: nocover
        cls.keep3rv1_contract = cast(
            Keep3rV1Contract, contract_registry.make(str(configuration.public_id))
        )

    @property
    def sender(self) -> Any:
        """Returns the default tx sender."""
        sender = crypto_registry.make(
            EthereumCrypto.identifier, private_key_path=self.private_key_path  # type: ignore
        )
        return sender

    def test_become_keeper(self) -> None:
        """Test become keeper"""

        default_gas_params = {
            "gas": DEFAULT_GAS,
            "maxFeePerGas": 5_000_000_000,
            "maxPriorityFeePerGas": 3_000_000_000,
        }
        amount = 1000
        kw = dict(address=self.sender.address)
        assert self.contract.is_keeper(**self.base_kw, **kw)["data"] is False

        # 0. Approve the contract to spend the tokens
        tx_data = self.keep3rv1_contract.build_approve_tx(
            self.ledger_api, self.dummy_erc20_token, self.contract_address, amount
        )
        raw_tx = {
            "from": self.sender.address,
            "to": self.dummy_erc20_token,
            "data": tx_data["data"],
            "value": 0,
            "chainId": self.ledger_api.api.eth.chain_id,
        }
        raw_tx.update(default_gas_params)
        self.perform_tx(raw_tx)

        # 1. bond - normally has a bonding period associated
        tx_data = self.contract.build_bond_tx(
            **self.base_kw, address=self.dummy_erc20_token, amount=amount
        )
        raw_tx = {
            "from": self.sender.address,
            "to": self.contract_address,
            "data": tx_data["data"],
            "value": 0,
            "chainId": self.ledger_api.api.eth.chain_id,
        }
        raw_tx.update(default_gas_params)
        self.perform_tx(raw_tx)

        # 2. wait bondTime - 3 days
        self.time_jump(5 * SECONDS_PER_DAY)

        # 3. activate
        tx_data = self.contract.build_activate_tx(
            **self.base_kw, address=self.dummy_erc20_token
        )
        raw_tx.update(
            {
                "data": tx_data["data"],
            }
        )
        self.perform_tx(raw_tx)

        # validate
        kw = dict(address=self.sender.address)
        assert self.contract.is_keeper(**self.base_kw, **kw)["data"] is True

    def perform_tx(self, raw_tx: Dict[str, Any]) -> JSONLike:
        """Perform the transaction"""
        nonce = Nonce(
            self.ledger_api.api.eth.get_transaction_count(self.sender.address)
        )
        raw_tx["nonce"] = nonce
        signed_tx = self.sender.sign_transaction(raw_tx)
        tx_digest = cast(
            str, self.ledger_api.send_signed_transaction(signed_tx, raise_on_try=True)
        )
        time.sleep(HALF_A_SECOND)
        self.mine_block()
        wait_for_condition(
            lambda: self.ledger_api.get_transaction_receipt(tx_digest) is not None,
            timeout=RECEIPT_TIMEOUT,
            period=HALF_A_SECOND,
        )
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_digest)
        if not tx_receipt or not tx_receipt["status"]:
            raise ValueError(f"transaction failed: {tx_receipt}")
        return tx_receipt
