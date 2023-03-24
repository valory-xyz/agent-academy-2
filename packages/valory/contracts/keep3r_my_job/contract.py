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

"""This module contains a contract wrapper for MyJob."""

import logging
from typing import Any

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/keep3r_my_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class Keep3rMyJobContract(Contract):
    """Wrapper for MyJob."""

    contract_id = PUBLIC_ID

    @classmethod
    def workable(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the workable flag from the contract."""

        contract = cls.get_instance(ledger_api, contract_address)
        workable = contract.functions.workable().call()
        return dict(data=workable)

    @classmethod
    def build_work_tx(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """
        Get the raw work transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param kwargs: keyword arguments

        :return: the raw transaction
        """
        contract = cls.get_instance(ledger_api, contract_address)
        data = contract.encodeABI(
            fn_name="workForCredits",
            args=[],
        )
        return dict(
            data=data,
        )
