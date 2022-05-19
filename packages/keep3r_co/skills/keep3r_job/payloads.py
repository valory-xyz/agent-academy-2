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

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class SafeExistencePayload(BaseTxPayload):
    """Represent a transaction payload of type 'safe_existence'."""

    transaction_type = TransactionType.SAFE_EXISTENCE

    def __init__(self, sender: str, vote: Optional[bool] = None, **kwargs: Any) -> None:
        """Initialize an 'safe_existence' transaction payload.

        :param sender: the sender (Ethereum) address
        :param vote: the vote whether a safe contract exists
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._vote = vote

    @property
    def vote(self) -> Optional[bool]:
        """Get the vote."""
        return self._vote

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(vote=self.vote) if self.vote is not None else {}


class BaseAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


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
