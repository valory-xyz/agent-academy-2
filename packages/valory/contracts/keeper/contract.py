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

"""This module contains the class to connect to an Gnosis Safe contract."""
import binascii
import logging
import secrets
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from eth_typing import ChecksumAddress, HexAddress, HexStr
from hexbytes import HexBytes
from packaging.version import Version
from py_eth_sig_utils.eip712 import encode_typed_data
from requests import HTTPError
from web3.exceptions import SolidityError, TransactionNotFound
from web3.types import Nonce, TxData, TxParams, Wei

from packages.valory.contracts.gnosis_safe_proxy_factory.contract import (
    GnosisSafeProxyFactoryContract,
)


PUBLIC_ID = PublicId.from_str("valory/keeper:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

# NULL_ADDRESS: str = "0x" + "0" * 40
# SAFE_CONTRACT = "0xd9Db270c1B5E3Bd161E8c8503c55cEABeE709552"
# DEFAULT_CALLBACK_HANDLER = "0xf48f2B2d2a534e402487b3ee7C18c33Aec0Fe5e4"
# PROXY_FACTORY_CONTRACT = "0xa6B71E26C5e0845f74c812102Ca7114b6a896AB2"
# SAFE_DEPLOYED_BYTECODE = "0x608060405273ffffffffffffffffffffffffffffffffffffffff600054167fa619486e0000000000000000000000000000000000000000000000000000000060003514156050578060005260206000f35b3660008037600080366000845af43d6000803e60008114156070573d6000fd5b3d6000f3fea2646970667358221220d1429297349653a4918076d650332de1a1068c5f3e07c5c82360c277770b955264736f6c63430007060033"


def _get_nonce() -> int:
    """Generate a nonce for the Safe deployment."""
    return secrets.SystemRandom().randint(0, 2 ** 256 - 1)


def checksum_address(agent_address: str) -> ChecksumAddress:
    """Get the checksum address."""
    return ChecksumAddress(HexAddress(HexStr(agent_address)))


class SafeOperation(Enum):
    """Operation types."""

    CALL = 0
    DELEGATE_CALL = 1
    CREATE = 2


class KeeperContract(Contract):
    """The Gnosis Safe contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_work_transaction(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        job_contract_address: str,
        sender_address: str,
        owners: Tuple[str],
        signatures_by_owner: Dict[str, str],
        safe_tx_gas: int = 0,
        base_gas: int = 0,
        gas_price: Optional[int] = None,
        nonce: Optional[Nonce] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[int] = None,
        old_tip: Optional[int] = None,
    ) -> JSONLike:
        """
        Get the raw work transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param sender_address: the address of the sender
        :param owners: the sequence of owners
        :param signatures_by_owner: mapping from owners to signatures
        :param operation: Operation type of Safe transaction
        :param safe_tx_gas: Gas that should be used for the Safe transaction
        :param base_gas: Gas costs for that are independent of the transaction execution
            (e.g. base transaction fee, signature check, payment of the refund)
        :param safe_gas_price: Gas price that should be used for the payment calculation
        :param gas_token: Token address (or `0x000..000` if ETH) that is used for the payment
        :param refund_receiver: Address of receiver of gas payment (or `0x000..000`  if tx.origin).
        :param gas_price: gas price
        :param nonce: the nonce
        :param max_fee_per_gas: max
        :param max_priority_fee_per_gas: max
        :param old_tip: the old `maxPriorityFeePerGas` in case that we are trying to resubmit a transaction.
        :return: the raw work transaction
        """
        sender_address = ledger_api.api.toChecksumAddress(sender_address)
        ledger_api = cast(EthereumApi, ledger_api)
        signatures = cls._get_packed_signatures(owners, signatures_by_owner)
        job_contract = cls.get_instance(ledger_api, job_contract_address)

        w3_tx = job_contract.functions.work()
        configured_gas = base_gas + safe_tx_gas + 75000
        tx_parameters: Dict[str, Union[str, int]] = {
            "from": sender_address,
            "gas": configured_gas,
        }
        if gas_price is not None:
            tx_parameters["gasPrice"] = gas_price
        if max_fee_per_gas is not None:
            tx_parameters["maxFeePerGas"] = max_fee_per_gas  # pragma: nocover
        if max_priority_fee_per_gas is not None:  # pragma: nocover
            tx_parameters["maxPriorityFeePerGas"] = max_priority_fee_per_gas
        if (
            gas_price is None
            and max_fee_per_gas is None
            and max_priority_fee_per_gas is None
        ):
            tx_parameters.update(ledger_api.try_get_gas_pricing(old_tip=old_tip))
        # note, the next line makes an eth_estimateGas call!
        transaction_dict = w3_tx.buildTransaction(tx_parameters)
        transaction_dict["gas"] = Wei(
            max(transaction_dict["gas"] + 75000, configured_gas)
        )
        if nonce is None:
            transaction_dict["nonce"] = ledger_api.api.eth.get_transaction_count(
                ledger_api.api.toChecksumAddress(sender_address)
            )
        else:
            transaction_dict["nonce"] = nonce  # pragma: nocover

        return transaction_dict

    @classmethod
    def _get_packed_signatures(
        cls, owners: Tuple[str], signatures_by_owner: Dict[str, str]
    ) -> bytes:
        """Get the packed signatures."""
        sorted_owners = sorted(owners, key=str.lower)
        signatures = b""
        for signer in sorted_owners:
            if signer not in signatures_by_owner:
                continue  # pragma: nocover
            signature = signatures_by_owner[signer]
            signature_bytes = binascii.unhexlify(signature)
            signatures += signature_bytes
        # Packed signature data ({bytes32 r}{bytes32 s}{uint8 v})
        return signatures

