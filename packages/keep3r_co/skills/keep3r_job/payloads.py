# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

from abc import ABC, abstractmethod
from collections.abc import Hashable
from enum import Enum
from typing import Any, Dict, Optional, Tuple

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


class TransactionType(Enum):
    """Enumeration of transaction types."""

    APPROVE_BOND = "approve_bond"
    SELECTED_PATH = "selected_path"
    TOP_UP = "top_up"
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


class BaseKeep3rJobPayload(BaseTxPayload, ABC):
    """Base class for the simple abci demo."""

    @property
    @abstractmethod
    def _data_keys(self) -> Tuple[str]:
        """Attributes to be retrieved and used as keys in .data()"""

    @property
    def data(self) -> Dict[str, Hashable]:
        """Get the data for this payload"""

        return {k: getattr(self, k) for k in self._data_keys}


class PathSelectionPayload(BaseKeep3rJobPayload):
    """PathSelectionPayload"""

    _data_keys: Tuple[str] = ("path_selection",)
    transaction_type = TransactionType.SELECTED_PATH

    def __init__(self, sender: str, path_selection: Hashable, **kwargs: Any) -> None:
        """Initialize a 'path_selection' payload.

        :param sender: the sender (Ethereum) address
        :param path_selection: the selected path
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._path_selection = path_selection

    @property
    def path_selection(self) -> Hashable:
        """Get path_selection"""
        return self._path_selection


class ApproveBondTxPayload(BaseKeep3rJobPayload):
    """ApproveBondTxPayload"""

    _data_keys: Tuple[str] = ("approval_tx",)
    transaction_type = TransactionType.APPROVE_BOND

    def __init__(self, sender: str, approval_tx: str, **kwargs: Any) -> None:
        """Initialize a 'approve_bond' payload.

        :param sender: the sender (Ethereum) address
        :param approval_tx: the approval transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._approval_tx = approval_tx

    @property
    def approval_tx(self) -> str:
        """Get approval tx"""
        return self._approval_tx


class BondingTxPayload(BaseKeep3rJobPayload):
    """BondingTxPayload"""

    _data_keys: Tuple[str] = ("bonding_tx",)
    transaction_type = TransactionType.BONDING_TX

    def __init__(self, sender: str, bonding_tx: str, **kwargs: Any) -> None:
        """Initialize a 'bonding_tx' payload.

        :param sender: the sender (Ethereum) address
        :param bonding_tx: the bonding transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._bonding_tx = bonding_tx

    @property
    def bonding_tx(self) -> str:
        """Get done_waiting"""
        return self._bonding_tx


class WaitingPayload(BaseKeep3rJobPayload):
    """WaitingPayload"""

    _data_keys: Tuple[str] = ("done_waiting",)
    transaction_type = TransactionType.DONE_WAITING

    def __init__(self, sender: str, done_waiting: bool, **kwargs: Any) -> None:
        """Initialize a 'done_waiting' payload.

        :param sender: the sender (Ethereum) address
        :param done_waiting: whether agent is done waiting
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._done_waiting = done_waiting

    @property
    def done_waiting(self) -> bool:
        """Get done_waiting"""
        return self._done_waiting


class ActivationTxPayload(BaseKeep3rJobPayload):
    """ActivationPayload"""

    _data_keys: Tuple[str] = ("activation_tx",)
    transaction_type = TransactionType.ACTIVATION_TX

    def __init__(self, sender: str, activation_tx: str, **kwargs: Any) -> None:
        """Initialize a 'activation_tx' payload.

        :param sender: the sender (Ethereum) address
        :param activation_tx: the activation transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._activation_tx = activation_tx

    @property
    def activation_tx(self) -> str:
        """Get the activation transaction"""
        return self._activation_tx


class TopUpPayload(BaseKeep3rJobPayload):
    """TopUpPayload"""

    _data_keys: Tuple[str] = ("top_up",)
    transaction_type = TransactionType.TOP_UP

    def __init__(self, sender: str, top_up: bool, **kwargs: Any) -> None:
        """Initialize a 'top_up' payload.

        :param sender: the sender (Ethereum) address
        :param top_up: increase in funds detected
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._top_up = top_up

    @property
    def top_up(self) -> bool:
        """Get top_up."""
        return self._top_up


class GetJobsPayload(BaseKeep3rJobPayload):
    """GetJobsPayload"""

    _data_keys: Tuple[str] = ("job_list",)
    transaction_type = TransactionType.JOB_LIST

    def __init__(self, sender: str, job_list: str, **kwargs: Any) -> None:
        """Initialize an 'get_jobs' transaction payload.

        :param sender: the sender (Ethereum) address
        :param job_list: The job list
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._job_list = job_list

    @property
    def job_list(self) -> str:
        """Get the job list."""
        return self._job_list


class JobSelectionPayload(BaseKeep3rJobPayload):
    """Represent a transaction payload of type 'job_selection'."""

    _data_keys: Tuple[str] = ("current_job",)
    transaction_type = TransactionType.JOB_SELECTION

    def __init__(self, sender: str, current_job: Optional[str], **kwargs: Any) -> None:
        """Initialize an 'job_selection' payload.

        :param sender: the sender (Ethereum) address
        :param current_job: selected job address
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._current_job = current_job

    @property
    def current_job(self) -> Optional[str]:
        """Get the current job selection."""
        return self._current_job


class IsWorkablePayload(BaseKeep3rJobPayload):
    """Represent a transaction payload of type 'is_workable'."""

    _data_keys: Tuple[str] = ("is_workable",)
    transaction_type = TransactionType.IS_WORKABLE

    def __init__(self, sender: str, is_workable: bool, **kwargs: Any) -> None:
        """Initialize an 'is_workable' payload.

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


class IsProfitablePayload(BaseKeep3rJobPayload):
    """Represent a transaction payload of type 'is_profitable'."""

    _data_keys: Tuple[str] = ("is_profitable",)
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


class WorkTxPayload(BaseKeep3rJobPayload):
    """Represent a transaction payload of type 'randomness'."""

    _data_keys: Tuple[str] = ("work_tx",)
    transaction_type = TransactionType.WORK_TX

    def __init__(self, sender: str, work_tx: str, **kwargs: Any) -> None:
        """Initialize a 'work_tx' payload.

        :param sender: the sender (Ethereum) address
        :param work_tx: the work transaction
        :param kwargs: the keyword arguments
        """
        super().__init__(sender, **kwargs)
        self._work_tx = work_tx

    @property
    def work_tx(self) -> str:
        """Get the work transaction"""
        return self._work_tx
