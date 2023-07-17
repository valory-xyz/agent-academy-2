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

"""This module contains the curve pool contract definition."""

import logging

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from web3 import Web3
from web3.types import BlockIdentifier

ENCODING = "utf-8"
PUBLIC_ID = PublicId.from_str("valory/curve_pool:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)


class CurvePoolContract(Contract):
    """The CurvePoolContract contract interface."""

    contract_id: PublicId = PUBLIC_ID

    @classmethod
    def get_dy(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        i: int,
        j: int,
        dx: int,
    ) -> JSONLike:
        """Get the dy value from the contract."""

        contract = cls.get_instance(ledger_api, contract_address)
        dy = contract.functions.get_dy(i, j, dx).call()
        return dict(data=dy)

    @classmethod
    def build_exchange_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        i: int,
        j: int,
        dx: int,
        min_dy: int,
        use_eth: bool = True,
    ) -> JSONLike:
        """Build curve exchange tx."""
        contract = cls.get_instance(ledger_api, contract_address)
        data = contract.encodeABI(
            fn_name="exchange",
            args=[
                i,
                j,
                dx,
                min_dy,
                use_eth,
            ],
        )
        return dict(data=data)

    @classmethod
    def get_token_transfer_events(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        buyer_address: str,
        from_block: BlockIdentifier = "earliest",
        to_block: BlockIdentifier = "latest",
    ) -> JSONLike:
        """Get the dy value from the contract."""
        contract = cls.get_instance(ledger_api, contract_address)
        entries = contract.events.TokenExchange.createFilter(
            fromBlock=from_block,
            toBlock=to_block,
            argument_filters=[{"buyer": Web3.toChecksumAddress(buyer_address)}],
        ).get_all_entries()
        return dict(
            data=list(
                map(
                    lambda entry: dict(
                        tx_hash=entry.transactionHash.hex(),
                        block_number=entry.blockNumber,
                    ),
                    entries,
                )
            )
        )
