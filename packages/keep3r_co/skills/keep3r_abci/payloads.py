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

"""This module contains the transaction payloads for the preliminary check of safe contract existence in the keep3r abci app."""

from enum import Enum
from typing import Any, Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

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
