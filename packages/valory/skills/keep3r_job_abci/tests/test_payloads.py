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

"""Test the payloads module of the skill."""
import json
from typing import List

import pytest

from packages.valory.skills.keep3r_job_abci.payloads import (
    ActivationTxPayload,
    ApproveBondTxPayload,
    BondingTxPayload,
    CalculateSpentGasPayload,
    GetJobsPayload,
    PathSelectionPayload,
    SwapAndDisburseRewardsPayload,
    UnbondingTxPayload,
    WaitingPayload,
    WorkTxPayload,
)
from packages.valory.skills.keep3r_job_abci.rounds import PathSelectionRound


@pytest.mark.parametrize("path_selection", PathSelectionRound.transitions)
def test_path_selection_payload(path_selection: str) -> None:
    """Test PathSelectionPayload"""

    payload = PathSelectionPayload(sender="sender", path_selection=path_selection)
    assert payload.sender == "sender"
    assert payload.path_selection == path_selection
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("bonding_tx", ["tx_hash"])
def test_bonding_tx_payload(bonding_tx: str) -> None:
    """Test BondingTxPayload"""

    payload = BondingTxPayload(sender="sender", bonding_tx=bonding_tx)
    assert payload.sender == "sender"
    assert payload.bonding_tx == bonding_tx
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("unbonding_tx", ["tx_hash"])
def test_unbonding_tx_payload(unbonding_tx: str) -> None:
    """Test UnbondingTxPayload"""

    payload = UnbondingTxPayload(sender="sender", unbonding_tx=unbonding_tx)
    assert payload.sender == "sender"
    assert payload.unbonding_tx == unbonding_tx
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("approval_tx", ["tx_hash"])
def test_approve_bond_tx_payload(approval_tx: str) -> None:
    """Test UnbondTxPayload"""

    payload = ApproveBondTxPayload(sender="sender", approval_tx=approval_tx)
    assert payload.sender == "sender"
    assert payload.approval_tx == approval_tx
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("done_waiting", [True, False])
def test_waiting_payload(done_waiting: bool) -> None:
    """Test WaitingPayload"""

    payload = WaitingPayload(sender="sender", done_waiting=done_waiting)
    assert payload.sender == "sender"
    assert payload.done_waiting == done_waiting
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("activation_tx", ["tx_hash"])
def test_activation_tx_payload(activation_tx: str) -> None:
    """Test ActivationTxPayload"""

    payload = ActivationTxPayload(sender="sender", activation_tx=activation_tx)
    assert payload.sender == "sender"
    assert payload.activation_tx == activation_tx
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("job_list", [[], ["job_address"]])
def test_get_jobs_payload(job_list: List[str]) -> None:
    """Test GetJobsPayload"""
    stringified_list = json.dumps(job_list)
    payload = GetJobsPayload(sender="sender", job_list=stringified_list)
    assert payload.sender == "sender"
    assert payload.job_list == stringified_list
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("work_tx", ["tx_hash"])
def test_work_tx_payload(work_tx: str) -> None:
    """Test WorkTxPayload"""

    payload = WorkTxPayload(sender="sender", work_tx=work_tx)
    assert payload.sender == "sender"
    assert payload.work_tx == work_tx
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("address_to_gas_spent", ["{address: gas_spent}"])
def test_calculate_spent_gas_payload(address_to_gas_spent: str) -> None:
    """Test CalculateSpentGasPayload"""

    payload = CalculateSpentGasPayload(
        sender="sender", address_to_gas_spent=address_to_gas_spent
    )
    assert payload.sender == "sender"
    assert payload.address_to_gas_spent == address_to_gas_spent
    assert payload.from_json(payload.json) == payload


@pytest.mark.parametrize("swap_and_disburse_tx", ["tx_hash"])
def test_swap_and_disburse_rewards_payload(swap_and_disburse_tx: str) -> None:
    """Test SwapAndDisburseRewardsPayload"""

    payload = SwapAndDisburseRewardsPayload(
        sender="sender", swap_and_disburse_tx=swap_and_disburse_tx
    )
    assert payload.sender == "sender"
    assert payload.swap_and_disburse_tx == swap_and_disburse_tx
    assert payload.from_json(payload.json) == payload
