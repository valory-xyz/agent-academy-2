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
from typing import List

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

GOERLI_CONTRACT_ADDRESS = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"
MAINNET_CONTRACT_ADDRESS = "0x1cEB5cB57C4D4E2b2433641b95Dd330A33185A44"


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
        tx_parameters["gasPrice"] = Wei(int(ledger_api.api.eth.gas_price))
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
