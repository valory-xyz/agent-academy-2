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

"""Test the payloads.py module of the skill."""

from typing import List

import pytest

from packages.keep3r_co.skills.keep3r_job.payloads import (
    GetJobsPayload,
    IsProfitablePayload,
    TransactionType,
    WorkTxPayload,
)


@pytest.mark.parametrize("job_list", [[], ["job_address"]])
def test_get_jobs_payload(job_list: List[str]) -> None:
    """Test `IsProfitablePayload`"""

    payload = GetJobsPayload(sender="sender", job_list=job_list)
    assert payload.sender == "sender"
    assert payload.job_list == tuple(job_list)
    assert payload.transaction_type == TransactionType.JOB_LIST


def test_preparetx_payload() -> None:
    """Test `TXHashPayload`"""

    payload = WorkTxPayload(sender="sender", tx_hash="test_hash")

    assert payload.sender == "sender"
    assert payload.tx_hash == "test_hash"
    assert payload.transaction_type == TransactionType.WORK_TX


def test_is_profitable_payload() -> None:
    """Test `IsProfitablePayload`"""

    payload = IsProfitablePayload(sender="sender", is_profitable=True)

    assert payload.sender == "sender"
    assert payload.is_profitable is True
    assert payload.transaction_type == TransactionType.IS_PROFITABLE
