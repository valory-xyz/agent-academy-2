# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This module contains helper classes for IPFS interaction."""
import json
from typing import Dict

import yaml

from packages.valory.skills.abstract_round_abci.io_.load import Loader
from packages.valory.skills.abstract_round_abci.io_.store import SupportedObjectType


class ContractPackageLoader(Loader):
    """Contract package loader."""

    def load(self, serialized_objects: Dict[str, str]) -> SupportedObjectType:
        """
        Load a contract package.

        Note this loader is to be used with ethereum contract packages ONLY!

        :param serialized_objects: the serialized objects.
        :return: the contract.yaml, contract.py and abi as a tuple.
        """
        # the contract package MUST contain a contract.yaml and contract.py file
        if (
            "contract.yaml" not in serialized_objects
            or "contract.py" not in serialized_objects
        ):
            raise ValueError(
                "Invalid contract package. "
                "The contract package MUST contain a contract.yaml and contract.py file."
            )

        # load the contract.yaml file
        contract_yaml = yaml.safe_load(serialized_objects["contract.yaml"])
        if (
            "contract_interface_paths" not in contract_yaml
            or "ethereum" not in contract_yaml["contract_interface_paths"]
        ):
            raise ValueError(
                "Invalid contract package. "
                "The contract.yaml file MUST contain a 'contract_interface' key."
            )

        # load the contract abi
        contract_abi_path = contract_yaml["contract_interface_paths"]["ethereum"]
        if contract_abi_path not in serialized_objects:
            raise ValueError(
                f"Invalid contract package. "
                f"{contract_abi_path} is not present in the contract package."
            )
        abi_json = json.loads(serialized_objects[contract_abi_path])
        return contract_yaml, serialized_objects["contract.py"], abi_json
