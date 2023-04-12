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

"""This module contains the transaction payloads for the keep3r_job_abci app."""

from dataclasses import dataclass

from packages.valory.skills.abstract_round_abci.base import BaseTxPayload


@dataclass(frozen=True)
class PathSelectionPayload(BaseTxPayload):
    """PathSelectionPayload"""

    path_selection: str


@dataclass(frozen=True)
class ApproveBondTxPayload(BaseTxPayload):
    """ApproveBondTxPayload"""

    approval_tx: str


@dataclass(frozen=True)
class BondingTxPayload(BaseTxPayload):
    """BondingTxPayload"""

    bonding_tx: str


@dataclass(frozen=True)
class WaitingPayload(BaseTxPayload):
    """WaitingPayload"""

    done_waiting: bool


@dataclass(frozen=True)
class ActivationTxPayload(BaseTxPayload):
    """ActivationPayload"""

    activation_tx: str


@dataclass(frozen=True)
class TopUpPayload(BaseTxPayload):
    """TopUpPayload"""

    top_up: bool


@dataclass(frozen=True)
class GetJobsPayload(BaseTxPayload):
    """GetJobsPayload"""

    job_list: str


@dataclass(frozen=True)
class IsWorkablePayload(BaseTxPayload):
    """Represent a transaction payload of type 'is_workable'."""

    workable_job: str


@dataclass(frozen=True)
class IsProfitablePayload(BaseTxPayload):
    """Represent a transaction payload of type 'is_profitable'."""

    is_profitable: bool


@dataclass(frozen=True)
class WorkTxPayload(BaseTxPayload):
    """Represent a transaction payload of type 'randomness'."""

    work_tx: str
