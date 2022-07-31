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
from typing import Any, Dict, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, TxParams, Wei


PUBLIC_ID = PublicId.from_str("valory/goerli_keep3r_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

NULL_ADDRESS: str = "0x" + "0" * 40
CONTRACT_ADDRESS = "0xd50345ca88e0B2cF9a6f5eD29C1F1f9d76A16C3c"


class GoerliKeep3rTestJob(Contract):
    """The scaffold contract class for a smart contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_RAW_TRANSACTION' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> bytes:
        """
        Handler method for the 'GET_RAW_MESSAGE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Handler method for the 'GET_STATE' requests.

        Implement this method in the sub class if you want
        to handle the contract requests manually.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param kwargs: the keyword arguments.
        :return: the tx  # noqa: DAR202
        """
        raise NotImplementedError

    @classmethod
    def get_gas_price(cls, ledger_api: LedgerApi) -> Optional[Wei]:
        """Get the gas price."""
        ethereum_api = cast(EthereumApi, ledger_api)
        gas_price = ethereum_api.api.eth.generate_gas_price()
        return gas_price

    @classmethod
    def get_workable(
        cls, ledger_api: LedgerApi, contract_address: str
    ) -> Optional[bool]:
        """Get the workable flag from the contract."""
        ethereum_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ethereum_api, contract_address)
        workable = contract.functions.workable().call()
        return workable

    @classmethod
    def work(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        job_contract_address: str,
        sender_address: str,
        gas: Optional[int] = None,
        gas_price: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        nonce: Optional[Nonce] = None,
    ) -> Any:
        """
        Get the raw work transaction

        :param ledger_api: the ledger API object
        :param job_contract_address: the job contract address
        :param sender_address: the address of the sender
        :param gas: Gas
        :param gas_price: gas price
        :param max_fee_per_gas: max
        :param max_priority_fee_per_gas: max
        :param nonce: the nonce

        :return: the transaction
        """

        ledger_api = cast(EthereumApi, ledger_api)
        job_contract = cls.get_instance(ledger_api, job_contract_address)

        tx_parameters = TxParams({"from": sender_address})

        if gas_price is not None:
            tx_parameters["gasPrice"] = Wei(gas_price)  # pragma: nocover

        if max_fee_per_gas is not None:
            tx_parameters["maxFeePerGas"] = Wei(max_fee_per_gas)  # pragma: nocover

        if max_priority_fee_per_gas is not None:
            tx_parameters["maxPriorityFeePerGas"] = Wei(  # pragma: nocover
                max_priority_fee_per_gas
            )

        if gas_price is max_fee_per_gas is max_priority_fee_per_gas is None:
            tx_parameters.update(ledger_api.try_get_gas_pricing())

        if gas is not None:
            tx_parameters["gas"] = Wei(gas)

        if nonce is not None:
            tx_parameters["nonce"] = Nonce(nonce)

        work_transaction_dict = job_contract.functions.work().buildTransaction(
            tx_parameters
        )
        # Auto estimation of gas does not work. We use a little more gas just in case
        work_transaction_dict["gas"] = Wei(work_transaction_dict["gas"] + 50000)

        result = dict(cast(Dict, work_transaction_dict))

        return result
