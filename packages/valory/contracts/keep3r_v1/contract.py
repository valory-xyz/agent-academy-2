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
from typing import Dict, Union

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from web3.types import Nonce, TxParams, Wei

from packages.valory.contracts.keep3r_v1_library.contract import (  # type: ignore # noqa: F401
    PUBLIC_ID as LIB_PUBLIC_ID,
)


ENCODING = "utf-8"
PUBLIC_ID = PublicId.from_str("valory/keep3r_v1:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


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
    def bond(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Bonding duration before one can activate to become a keeper"""

        contract = cls.get_instance(ledger_api, contract_address)
        bond = contract.functions.BOND().call()
        return dict(data=bond)

    @classmethod
    def bondings(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> JSONLike:
        """Tracks all current bond times (start)"""

        contract = cls.get_instance(ledger_api, contract_address)
        bondings = contract.functions.bondings(address, contract.address).call()
        return dict(data=bondings)

    @classmethod
    def blacklist(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> JSONLike:
        """Check blacklist of keepers not allowed to participate"""

        contract = cls.get_instance(ledger_api, contract_address)
        is_blacklisted = contract.functions.blacklist(address).call()
        return dict(data=is_blacklisted)

    @classmethod
    def credits(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> JSONLike:
        """Check current credit available for a job"""

        contract = cls.get_instance(ledger_api, contract_address)
        credits = contract.functions.credits(address, contract.address).call()
        return dict(data=credits)

    @classmethod
    def get_jobs(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """Full listing of all jobs ever added."""

        contract = cls.get_instance(ledger_api, contract_address)
        addresses = contract.functions.getJobs().call()
        return dict(data=addresses)

    @classmethod
    def is_keeper(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> JSONLike:
        """Check if address is a registered keeper."""

        contract = cls.get_instance(ledger_api, contract_address)
        is_keeper = contract.functions.isKeeper(keeper=address).call()
        return dict(data=is_keeper)

    @classmethod
    def build_add_job_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        job: str,
    ) -> RawTransaction:
        """Allows governance to add new job systems."""

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.addJob(job=job)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def build_approve_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        spender: str,
        amount: Union[Wei, int],
    ) -> RawTransaction:
        """Allows a keeper to activate/register themselves after bonding.

        Sets `amount` as the allowance of `spender` over the caller's tokens.
        After transaction submission, a boolean value indicating whether the operation
        succeeded is returned. Here we only build the raw transaction.

        IMPORTANT: Beware that changing an allowance with this method brings the risk
        that someone may use both the old and the new allowance by unfortunate
        transaction ordering. One possible solution to mitigate this race
        condition is to first reduce the spender's allowance to 0 and set the
        desired value afterwards:
        https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729

        :param ledger_api: the ledger api
        :param contract_address: the Keep3rV1 contract address
        :param address: the address with which to sign the raw transaction
        :param spender: The address of the account which may transfer tokens
        :param amount: The number of tokens that are approved (2^256-1 means infinite)

        :return: the raw transaction to be signed by the agents
        """

        contract = cls.get_instance(ledger_api, contract_address)
        function = contract.functions.approve(spender=spender, amount=amount)
        return function.buildTransaction(cls.get_tx_parameters(ledger_api, address))

    @classmethod
    def allowance(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        account: str,
        spender: str,
    ) -> JSONLike:
        """Get the number of tokens `spender` is approved to spend on behalf of `account`."""

        contract = cls.get_instance(ledger_api, contract_address)
        tx_kwargs = dict(spender=spender, account=account)
        allowance = contract.functions.allowance(**tx_kwargs).call()
        return dict(data=allowance)

    @classmethod
    def build_bond_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        amount: int,
    ) -> RawTransaction:
        """Begin the bonding process for a new keeper. Default bonding period takes 3 days."""
        contract = cls.get_instance(ledger_api, contract_address)
        data = contract.encodeABI(
            fn_name="bond",
            args=[
                address,
                amount,
            ],
        )
        return dict(
            data=data,
        )

    @classmethod
    def build_activate_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
    ) -> RawTransaction:
        """Allows a keeper to activate/register themselves after bonding."""

        contract = cls.get_instance(ledger_api, contract_address)
        data = contract.encodeABI(
            fn_name="activate",
            args=[
                address,
            ],
        )
        return dict(
            data=data,
        )

    @classmethod
    def build_unbond_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        address: str,
        amount: Union[Wei, int],
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
