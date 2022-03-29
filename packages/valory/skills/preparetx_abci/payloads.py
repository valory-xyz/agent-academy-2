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

"""This module contains the transaction payloads for the simple_abci app."""
from abc import ABC
from enum import Enum
from typing import Any, Dict

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    PREPARE_TX = "prepare_tx"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BasePrepareTxAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class PrepareTxPayload(BasePrepareTxAbciPayload):
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
    def round_id(self) -> int:
        """Get the round id."""
        return self._tx_hash

