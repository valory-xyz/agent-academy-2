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
"""This module contains utils for dynamically loading aea packages."""
import logging
from abc import ABC
from typing import Any, Dict, Optional, Type

from aea.configurations.base import ContractConfig
from aea.configurations.data_types import PublicId
from aea.contracts import Contract, contract_registry
from aea.crypto.registries.base import ItemId


_logger = logging.getLogger(__name__)


def load_contract(
    contract_py: str, contract_yaml: Dict[str, Any], abi_json: Dict[str, Any]
) -> Optional[PublicId]:
    """Load a contract dynamically."""
    # run the contract.py file to load the contract class into the global namespace
    # WARNING: should be used only if you trust the contents of contract_py
    exec(contract_py, globals())  # pylint: disable=exec-used; #nosec

    # check that the contract class, as defined in contract.yaml, is in the global namespace
    contract_config = ContractConfig(
        name=contract_yaml["name"],
        author=contract_yaml["author"],
        version=contract_yaml["version"],
        class_name=contract_yaml["class_name"],
    )
    expected_cls_name = contract_config.class_name
    if expected_cls_name not in globals():
        _logger.error(f"Contract class {expected_cls_name} not found in module.")
        return None

    # load the contract into the registry
    contract_cls = globals()[expected_cls_name]
    item_spec = DynamicItemSpec(contract_config, contract_cls, abi_json)
    item_id = ItemId(str(item_spec.id))
    contract_registry.specs[item_id] = item_spec  # type: ignore
    return item_spec.id


class DynamicItemSpec(ABC):
    """A class to represent dynamic contract spec."""

    def __init__(
        self,
        contract_config: ContractConfig,
        contract_cls: Type[Contract],
        contract_abi: Dict[str, Any],
    ) -> None:
        """Initialize the item specification."""
        self.id = contract_config.public_id
        self.contract_cls = contract_cls
        self._class_kwargs = {"contract_interface": {"ethereum": contract_abi}}
        self._kwargs = dict(contract_config=contract_config)
        for key, value in self._class_kwargs.items():
            setattr(self.contract_cls, key, value)

    def make(self, **kwargs: Any) -> Contract:
        """Make an instance of the item."""
        _kwargs = self._kwargs.copy()
        _kwargs.update(kwargs)
        return self.contract_cls(**_kwargs)

    def get_class(self) -> Type[Contract]:
        """Get the class of the item."""
        return self.contract_cls
