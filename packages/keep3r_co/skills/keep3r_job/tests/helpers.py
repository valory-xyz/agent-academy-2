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
# pylint: disable=unused-argument
"""Helpers for unit tests."""
from typing import Any, Callable, Dict, Generator, Optional

from packages.valory.skills.abstract_round_abci.io_.store import SupportedObjectType


contract_yaml = {
    "name": "deposit_manager_job",
    "author": "valory",
    "version": "0.1.0",
    "class_name": "DepositManagerJobContract",
    "contract_interface_paths": {"ethereum": "DepositManager.json"},
}
contract_py = """
class DepositManagerJobContract(Contract):
    \"\"\"Class for the DepositManagerJob contract.\"\"\"
"""
contract_json: Dict = {}

DUMMY_CONTRACT_PACKAGE = (contract_yaml, contract_py, contract_json)


def wrap_dummy_get_from_ipfs(return_value: Optional[SupportedObjectType]) -> Callable:
    """Wrap dummy_get_from_ipfs."""

    def dummy_get_from_ipfs(
        *args: Any, **kwargs: Any
    ) -> Generator[None, None, Optional[SupportedObjectType]]:
        """A mock get_from_ipfs."""
        return return_value
        yield

    return dummy_get_from_ipfs
