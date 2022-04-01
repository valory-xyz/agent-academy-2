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

"""This module contains the transaction payloads for the keep3r bot app."""
from abc import ABC
from enum import Enum
from typing import Any

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    IS_WORKABLE = "is_workable"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value



class BaseAbciPayload(BaseTxPayload, ABC):
    """Base class for an abci payload."""

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
