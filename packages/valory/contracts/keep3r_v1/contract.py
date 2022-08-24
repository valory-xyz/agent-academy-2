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

"""This module contains the Keep3rV1 contract definition."""

import logging
from typing import Dict, List, Union

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from web3.contract import ChecksumAddress
from web3.types import Nonce, TxParams, Wei


ENCODING = "utf-8"
PUBLIC_ID = PublicId.from_str("valory/keep3r_v1:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

GAS_MULTIPLIER = 1.1
NULL_ADDRESS: str = "0x" + "0" * 40

# Keep3rV1ForTest - Goerli
KEEP3R_V1_FOR_TEST = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"
KEEP3R_HELPER_FOR_TEST = "0x2720535578096f1dE6C8c9B5255F1Bda40e8067A"

# Keep3rV1 - mainnet
KEEP3R_V1 = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"
KEEP3R_HELPER = "0xb41772890c8b1564c5015a12c0dc6f18b0af955e"

RawTransaction = Dict[str, Union[int, str]]


class Keep3rV1Contract(Contract):
    """
    Keep3r V1 contract interface. Covers existing contract methods only partially.

    To become a keeper:
    1. Call `approve`. No funds are required
    2. Call `bond`. No funds are required, however some jobs
       might require a minimum amount of funds bonded.
    3. After waiting `bondTime` (default 3 days) you can activate
       as keeper.

    source: https://docs.keep3r.network
    """

    contract_id: PublicId = PUBLIC_ID

    @staticmethod
    def get_tx_parameters(ledger_api: EthereumApi, address: str) -> TxParams:
        """Get transaction parameters."""

        tx_parameters = TxParams()
        nonce = Nonce(ledger_api.api.eth.get_transaction_count(address))
        tx_parameters["from"] = ledger_api.api.toChecksumAddress(address)
        tx_parameters["nonce"] = nonce
        tx_parameters["gas"] = ledger_api.api.eth.estimate_gas(tx_parameters)
        tx_parameters.update(ledger_api.try_get_gas_pricing())
        _logger.info(f"tx_parameters: {tx_parameters}")

        return tx_parameters

    @classmethod
    def get_jobs(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> List[ChecksumAddress]:
        """Full listing of all jobs ever added."""

        contract = cls.get_instance(ledger_api, contract_address)
        return contract.functions.getJobs().call()

    @classmethod
    def is_keeper(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> bool:
        """Check if address is a registered keeper."""

        contract = cls.get_instance(ledger_api, contract_address)
        return contract.functions.isKeeper(keeper=address).call()

    @classmethod
    def build_approve_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        amount: Wei,
    ) -> RawTransaction:
        """Allows a keeper to activate/register themselves after bonding."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.approve(spender=contract.address, amount=amount)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def build_bond_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        amount: Wei,
    ) -> RawTransaction:
        """Begin the bonding process for a new keeper. Default bonding period takes 3 days."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.bond(bonding=contract.address, amount=amount)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def build_activate_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> RawTransaction:
        """Allows a keeper to activate/register themselves after bonding."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.activate(bonding=contract.address)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def build_unbond_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        amount: Wei,
    ) -> RawTransaction:
        """Begin the unbonding process to stop being a keeper. Default unbonding period is 14 days."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.unbond(bonding=contract.address, amount=amount)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def build_withdraw_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> RawTransaction:
        """Withdraw funds after unbonding has finished."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.withdraw(bonding=contract.address)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))
