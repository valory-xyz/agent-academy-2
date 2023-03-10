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
# pylint: disable=no-member
"""Python package extending the default open-aea ethereum ledger plugin to add support for flashbots."""

import logging
from typing import Any, Dict, List, Optional, cast
from uuid import uuid4

from aea_ledger_ethereum import EthereumApi
from eth_account import Account
from eth_account.datastructures import SignedTransaction
from flashbots import flashbot
from web3 import Web3
from web3.exceptions import TransactionNotFound


_default_logger = logging.getLogger(__name__)


class EthereumFlashbotApi(EthereumApi):
    """Class to interact with the Ethereum Web3 APIs."""

    def __init__(self, **kwargs: Any):
        """
        Initialize the Ethereum API.

        :param kwargs: the keyword arguments.
        """
        super().__init__(**kwargs)
        w3 = cast(Web3, self.api)
        signature_private_key = kwargs.pop("signature_private_key", None)
        if signature_private_key is not None:
            signature_account = (
                Account.from_key(  # pylint: disable=no-value-for-parameter
                    private_key=signature_private_key
                )
            )
        else:
            signature_account = (
                Account.create()  # pylint: disable=no-value-for-parameter
            )

        flashbot_relayer_uri = kwargs.pop("flashbot_relayer_uri", None)
        # if flashbot_relayer_uri is None, the default URI is used
        flashbot(w3, signature_account, flashbot_relayer_uri)

    def bundle_transactions(  # pylint: disable=no-self-use
        self, signed_transactions: List[SignedTransaction]
    ) -> List[Dict[str, Any]]:
        """Bundle transactions."""
        bundle = [
            {"signed_transaction": signed_transaction.rawTransaction}
            for signed_transaction in signed_transactions
        ]
        return bundle

    def simulate(
        self,
        bundle: List[Dict[str, Any]],
        target_block: Optional[int],
    ) -> bool:
        """
        Simulate a bundle.

        1. Simulate the bundle in a try catch block.
        2. Return whether True if simulation went through, or False if something went wrong.

        :param bundle: the bundle to simulate.
        :param target_block: the target block for the transaction, the current block if not provided.
        :return: True if the simulation went through, False otherwise.
        """
        _default_logger.debug(f"Simulating bundle: {bundle}")
        try:
            self.api.flashbots.simulate(bundle, target_block)
            _default_logger.debug(f"Simulation successful for bundle {bundle}.")
            return True
        except Exception as e:  # pylint: disable=broad-except
            _default_logger.warning(f"Simulation failed for bundle {bundle}: {e}")
        return False

    def send_bundle(
        self,
        bundle: List[Dict[str, Any]],
        target_blocks: List[int],
    ) -> Optional[List[str]]:
        """
        Send a bundle.

        1. Simulate the bundle.
        2. Send the bundle in a try catch block.
        3. Wait for the response. If successful, go to step 3. If current block number is less than the maximum target block number, go to step 1.
        4. Return the transaction digest if the transaction went through, or None if something went wrong.

        :param bundle: the signed transactions to bundle together and send.
        :param target_blocks: the target blocks for the transactions.
        :return: the transaction digest if the transaction went through, None otherwise.
        """
        for target_block in target_blocks:
            if not self.simulate(bundle, target_block):
                _default_logger.warning(
                    f"Simulation failed for bundle {bundle} targeting block {target_block}."
                )
                continue

            replacement_uuid = str(uuid4())
            _default_logger.debug(
                f"Sending bundle {bundle} with replacement_uuid {replacement_uuid} targeting block {target_block}"
            )
            response = self.api.flashbots.send_bundle(
                bundle, target_block, opts={"replacementUuid": replacement_uuid}
            )
            _default_logger.debug(
                f"Response from bundle with replacement uuid {replacement_uuid}: {response}"
            )
            response.wait()
            try:
                receipts = response.receipts()
                tx_hashes = [tx["hash"] for tx in response.bundle]
                logging.debug(
                    f"Bundle with replacement uuid {replacement_uuid} was mined in block {receipts[0]['blockNumber']}"
                    f"Tx hashes: {tx_hashes}"
                )
                return tx_hashes
            except TransactionNotFound:
                # get & log the bundle stats in case it was not included in the block
                stats = self.api.flashbots.get_bundle_stats_v2(
                    self.api.toHex(response.bundle_hash()), target_block
                )
                logging.debug(
                    f"Bundle with replacement uuid {replacement_uuid} not found in block {target_block}. "
                    f"bundle stats: {stats}"
                )
                # essentially a no-op but it shows that the function works
                cancel_res = self.api.flashbots.cancel_bundles(replacement_uuid)
                logging.debug(
                    f"Response from canceling bundle with replacement uuid {replacement_uuid}: {cancel_res}"
                )
        return None

    def bundle_and_send(
        self,
        signed_transactions: List[SignedTransaction],
        target_blocks: List[int],
    ) -> Optional[List[str]]:
        """
        Simulate and send a bundle of transactions.

        :param signed_transactions: the signed transactions to bundle together and send.
        :param target_blocks: the target blocks for the transactions.
        :return: the transaction digest if the transactions went through, None otherwise.
        """
        bundle = self.bundle_transactions(signed_transactions)
        tx_hashes = self.send_bundle(bundle, target_blocks)
        return tx_hashes
