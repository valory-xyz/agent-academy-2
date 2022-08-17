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

"""This module contains the scaffold contract definition."""

import logging
from typing import Dict, Optional, Union

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, TxParams


PUBLIC_ID = PublicId.from_str("valory/keep3r_test_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

NULL_ADDRESS: str = "0x" + "0" * 40
GOERLI_CONTRACT_ADDRESS = "0xd50345ca88e0B2cF9a6f5eD29C1F1f9d76A16C3c"


class Keep3rTestJobContract(Contract):
    """The scaffold contract class for a smart contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def workable(cls, ledger_api: EthereumApi, contract_address: str) -> Optional[bool]:
        """Get the workable flag from the contract."""

        contract = cls.get_instance(ledger_api, contract_address)
        return contract.functions.workable().call()

    @classmethod
    def build_work_tx(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> Dict[str, Union[int, str]]:
        """
        Get the raw work transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param address: the address of the sender

        :return: the raw transaction
        """

        contract = cls.get_instance(ledger_api, contract_address)

        tx_parameters = TxParams()
        nonce = Nonce(ledger_api.api.eth.get_transaction_count(address))
        tx_parameters["from"] = address
        tx_parameters["nonce"] = nonce
        tx_parameters["gas"] = ledger_api.api.eth.estimate_gas(tx_parameters)
        tx_parameters.update(ledger_api.try_get_gas_pricing())
        _logger.info(f"tx_parameters: {tx_parameters}")

        function = contract.functions.work()

        return function.buildTransaction(tx_parameters)
