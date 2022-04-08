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

"""This module contains the class to connect to a Price Oracle contract."""
import logging
from typing import Any, Optional, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea_ledger_ethereum import EthereumApi
from web3 import Web3
from web3.types import Wei


PUBLIC_ID = PublicId.from_str("philippb/price_oracle:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

CONTRACT_ADDRESS = "0xe7015CCb7E5F788B8c1010FC22343473EaaC3741"


class PriceOracleContract(Contract):
    """The Price Oracle contract."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_raw_transaction(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get the Safe transaction."""
        raise NotImplementedError

    @classmethod
    def get_raw_message(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[bytes]:
        """Get raw message."""
        raise NotImplementedError

    @classmethod
    def get_state(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Get state."""
        raise NotImplementedError

    @classmethod
    def get_kp3r_eth_price(
        cls, ledger_api: LedgerApi, contract_address: str, **kwargs: Any
    ) -> Optional[Wei]:
        """Request K3PR/ETH price"""
        ethereum_api = cast(EthereumApi, ledger_api)
        contract = cls.get_instance(ethereum_api, contract_address)
        response = contract.functions.latestRoundData().call()
        return response[1]