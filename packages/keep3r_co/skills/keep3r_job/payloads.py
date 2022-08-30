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

    PATH_SELECTION = "path_selection"
    BONDING_TX = "bonding_tx"
    DONE_WAITING = "done_waiting"
    ACTIVATION_TX = "activation_tx"
    JOB_LIST = "job_list"
    JOB_SELECTION = "job_selection"
    IS_WORKABLE = "is_workable"
    IS_PROFITABLE = "is_profitable"
    WORK_TX = "work_tx"

    def __str__(self) -> str:
        """Get the string value of the transaction type."""
        return self.value


class BaseAbciPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    def __hash__(self) -> int:
        """Hash the payload."""
        return hash(tuple(sorted(self.data.items())))


class PathSelectionPayload(BaseAbciPayload):
    """PathSelectionPayload"""

    transaction_type = TransactionType.PATH_SELECTION

    def __init__(self, sender: str, selected_path: str, **kwargs: Any) -> None:
        """Initialize an 'safe_existence' transaction payload.

        :param sender: the sender (Ethereum) address
        :param selected_path: selected path to traverse
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._selected_path = selected_path

    @property
    def selected_path(self) -> str:
        """Get the selected path to traverse."""
        return self._selected_path

    @property
    def data(self) -> Dict:
        """Get the data."""
        return dict(selected_path=self.selected_path)


class JobSelectionPayload(BaseAbciPayload):
    """Represent a transaction payload of type 'job_selection'."""

    transaction_type = TransactionType.JOB_SELECTION

    def __init__(self, sender: str, job_selection: Any, **kwargs: Any) -> None:
        """Initialize an 'select_keeper' transaction payload.

        :param sender: the sender (Ethereum) address
        :param job_selection: Select a job
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._job_selection = job_selection

    @property
    def job_selection(self) -> Optional[Any]:
        """Get the job selection."""
        return self._job_selection

    @property
    def data(self) -> Dict[str, Optional[Any]]:
        """Get the data."""
        return (
            dict(job_selection=self.job_selection)
            if self._job_selection is not None
            else {}
        )


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

    transaction_type = TransactionType.WORK_TX

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

    # Why do I have to set this transaction type here if it's not used anywhere else?
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
        """Get whether the contract is profitable."""
        return self._is_profitable

    @property
    def data(self) -> Dict[str, Optional[bool]]:
        """Get the data."""
        return (
            dict(is_profitable=self.is_profitable)
            if self.is_profitable is not None
            else {}
        )
