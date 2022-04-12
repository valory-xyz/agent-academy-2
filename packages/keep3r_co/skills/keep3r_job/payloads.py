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

"""This module contains the transaction payloads for the keep3r_job app."""
from abc import ABC
from enum import Enum
from typing import Any, Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    PREPARE_TX = "prepare_tx"
    RANDOMNESS = "randomness"
    SIGNATURE = "signature"
    IS_PROFITABLE = "is_profitable"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class TXHashPayload(BaseAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.PREPARE_TX

    def __init__(
            self, sender: str, tx_hash: str, **kwargs: Any
    ) -> None:
        """Initialize an 'prepare_tx' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the hash of the raw transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._tx_hash = tx_hash

    @property
    def round_id(self) -> TransactionType:
        """Get the round id."""
        return self.transaction_type

    @property
    def tx_hash(self) -> str:
        """Get the tx hash"""
        return self._tx_hash


class SignaturePayload(BaseTxPayload):
    """Represent a transaction payload of type 'signature'."""

    transaction_type = TransactionType.SIGNATURE

    def __init__(self, sender: str, signature: str, **kwargs: Any) -> None:
        """Initialize an 'signature' transaction payload.

        :param sender: the sender (Ethereum) address
        :param signature: the signature
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._signature = signature

    @property
    def signature(self) -> str:
        """Get the signature."""
        return self._signature

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(signature=self.signature)

class IsProfitablePayload(BaseAbciPayload):
    """Represent a transaction payload of type 'is_profitable'."""
    # Why do I have to set this transaction type here if its not used anywhere else?
    transaction_type = TransactionType.IS_PROFITABLE
    def __init__(self, sender: str, is_profitable: bool, **kwargs: Any) -> None:
        """Initialize an 'is_profitable' transaction payload.
        :param sender: the sender (Ethereum) address
        :param is_profitable: whether the job is profitable
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._is_profitable = is_profitable

    @property
    def is_profitable(self) -> bool:
        """Get whether the contract is workable."""
        return self._is_profitable

    @property
    def data(self) -> Dict[str, Optional[bool]]:
        """Get the data."""
        return dict(is_profitable=self.is_profitable) if self.is_profitable is not None else {}