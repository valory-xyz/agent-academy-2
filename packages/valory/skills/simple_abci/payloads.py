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
from typing import Dict, Optional

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    REGISTRATION = "registration"
    RANDOMNESS = "randomness"
    SELECT_KEEPER = "select_keeper"
    DO_WORK = "do_work"
    IS_WORKABLE = "is_workable"
    IS_PROFITABLE = "is_profitable"
    RESET = "reset"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseSimpleAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class RegistrationPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'registration'."""

    transaction_type = TransactionType.REGISTRATION


class DoWorkPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'do work'."""

    transaction_type = TransactionType.DO_WORK

    def __init__(self, sender: str, round_id: int, id_: Optional[str] = None) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id

    @property
    def do_work(self) -> bool:
        """Get to work."""
        return True

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(do_work=self.do_work)


class IsProfitablePayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'is profitable'."""

    transaction_type = TransactionType.IS_PROFITABLE

    def __init__(self, sender: str, round_id: int, id_: Optional[str] = None) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id

    @property
    def is_profitable(self) -> bool:
        """Determine if profitable."""
        return True

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(is_profitable=True)


class IsWorkablePayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'is workable'."""

    transaction_type = TransactionType.IS_WORKABLE

    def __init__(self, sender: str, round_id: int, id_: Optional[str] = None) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id

    @property
    def is_workable(self) -> bool:
        """Get the contract."""
        return True

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(is_workable=self.is_workable)


class RandomnessPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'randomness'."""

    transaction_type = TransactionType.RANDOMNESS

    def __init__(
        self, sender: str, round_id: int, randomness: str, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param round_id: the round id
        :param randomness: the randomness
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._round_id = round_id
        self._randomness = randomness

    @property
    def round_id(self) -> int:
        """Get the round id."""
        return self._round_id

    @property
    def randomness(self) -> str:
        """Get the randomness."""
        return self._randomness

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(round_id=self._round_id, randomness=self._randomness)


class SelectKeeperPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'select_keeper'."""

    transaction_type = TransactionType.SELECT_KEEPER

    def __init__(self, sender: str, keeper: str, id_: Optional[str] = None) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param keeper: the keeper selection
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._keeper = keeper

    @property
    def keeper(self) -> str:
        """Get the keeper."""
        return self._keeper

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(keeper=self.keeper)


class ResetPayload(BaseSimpleAbciPayload):
    """Represent a transaction payload of type 'reset'."""

    transaction_type = TransactionType.RESET

    def __init__(
        self, sender: str, period_count: int, id_: Optional[str] = None
    ) -> None:
        """Initialize an 'rest' transaction payload.

        :param sender: the sender (Ethereum) address
        :param period_count: the period count id
        :param id_: the id of the transaction
        """
        super().__init__(sender, id_)
        self._period_count = period_count

    @property
    def period_count(self) -> int:
        """Get the period_count."""
        return self._period_count

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(period_count=self.period_count)
