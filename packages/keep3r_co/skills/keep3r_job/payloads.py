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
    SAFE_EXISTENCE = "safe_existence"
    IS_WORKABLE = "is_workable"
    IS_PROFITABLE = "is_profitable"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class SafeExistencePayload(BaseTxPayload):
    """Represent a transaction payload of type 'safe_existence'."""

    transaction_type = TransactionType.SAFE_EXISTENCE

    def __init__(
        self, sender: str, safe_exists: Optional[bool] = None, **kwargs: Any
    ) -> None:
        """Initialize an 'safe_existence' transaction payload.

        :param sender: the sender (Ethereum) address
        :param safe_exists: the safe_exists whether a safe contract exists
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._safe_exists = safe_exists

    @property
    def safe_exists(self) -> Optional[bool]:
        """Get the safe_exists."""
        return self._safe_exists

    @property
    def data(self) -> Dict:
        """Get the data."""
        return (
            dict(safe_exists=self.safe_exists) if self.safe_exists is not None else {}
        )


class BaseAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class IsWorkablePayload(BaseAbciPayload):
    """Represent a transaction payload of type 'is_workable'."""

    transaction_type = TransactionType.IS_WORKABLE

    def __init__(self, sender: str, is_workable: bool, **kwargs: Any) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param is_workable: whether the contract is workable
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._is_workable = is_workable

    @property
    def is_workable(self) -> bool:
        """Get whether the contract is workable."""
        return self._is_workable

    @property
    def data(self) -> Dict[str, Optional[bool]]:
        """Get the data."""
        return (
            dict(is_workable=self.is_workable) if self._is_workable is not None else {}
        )


class TXHashPayload(BaseAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.PREPARE_TX

    def __init__(self, sender: str, tx_hash: Optional[str], **kwargs: Any) -> None:
        """Initialize an 'prepare_tx' transaction payload.

        :param sender: the sender (Ethereum) address
        :param tx_hash: the hash of the raw transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._tx_hash = tx_hash

    @property
    def tx_hash(self) -> Optional[str]:
        """Get the tx hash"""
        return self._tx_hash

    @property
    def data(self) -> Dict[str, Optional[str]]:
        """Get the data."""
        return dict(tx_hash=self.tx_hash) if self.tx_hash is not None else {}


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
        return (
            dict(is_profitable=self.is_profitable)
            if self.is_profitable is not None
            else {}
        )
