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

"""This module contains the class to connect to a Keep3r Job contract."""
import logging
from typing import Any, Dict, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, TxParams, Wei


PUBLIC_ID = PublicId.from_str("valory/keep3r_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

NULL_ADDRESS: str = "0x" + "0" * 40
CONTRACT_ADDRESS = "0x2150b45626199CFa5089368BDcA30cd0bfB152D6"


class Keep3rJobContract(Contract):
    """The Keep3r Job contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @classmethod
    def get_workable(cls, ledger_api: LedgerApi, contract_address: str) -> JSONLike:
        """Get the workable flag from the contract."""
        ethereum_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ethereum_api, contract_address)
        workable = contract.functions.workable().call()
        return dict(data=workable)

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

        if (
            gas_price is None
            and max_fee_per_gas is None
            and max_priority_fee_per_gas is None
        ):
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

    @classmethod
    def reward_multiplier(
        cls, ledger_api: LedgerApi, contract_address: str
    ) -> JSONLike:
        """Gets the reward multiplier for the specific job."""
        ethereum_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ethereum_api, contract_address)
        reward_multiplier = contract.functions.rewardMultiplier().call()
        return dict(data=reward_multiplier)
