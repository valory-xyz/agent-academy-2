# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains the Keep3rV1 contract definition."""

import json
import logging
from pathlib import Path
from typing import List

from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from web3 import Web3
from web3.contract import ChecksumAddress
from web3.contract import Contract as Web3Contract
from web3.contract import ContractFunction
from web3.types import Nonce, TxParams, TxReceipt, Wei


ENCODING = "utf-8"
PUBLIC_ID = PublicId.from_str("valory/keep3r_v1:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

GAS_MULTIPLIER = 1.1
NULL_ADDRESS: str = "0x" + "0" * 40
CONTRACT_ADDRESS = "0x3364BF0a8DcB15E463E6659175c90A57ee3d4288"


class Keep3rV1Contract(Contract, Web3Contract):
    """
    Keep3r V1 contract interface. Covers existing contract methods only partially.

    To become a keeper:
    1. Call `approve`. No funds are required
    2. Call `bond`. No funds are required, however some jobs
       might require a minimum amount of funds bonded.
    3. After waiting `bondTime` (default 3 days) you can activate
       as keeper.

    source: https://docs.keep3r.network
    """

    web3: Web3
    contract_id: PublicId = PUBLIC_ID
    address: ChecksumAddress = Web3.toChecksumAddress(CONTRACT_ADDRESS)
    interface_path = list(Path(".").glob("**/Keep3rV1.json")).pop()
    interface = json.loads(interface_path.read_text(encoding=ENCODING))

    def __init__(self) -> None:
        """Initialize"""
        Contract.__init__(self, self.contract_interface)
        Web3Contract.__init__(self, self.address)

    @property
    def contract(self) -> Web3Contract:
        """Contract instance"""

        address, abi = self.address, self.interface["abi"]
        return self.web3.eth.contract(address=address, abi=abi)

    def get_jobs(self) -> List[ChecksumAddress]:
        """Full listing of all jobs ever added."""

        return self.functions.getJobs().call()

    def is_keeper(self, address: str) -> bool:
        """Check if address is a registered keeper."""

        return self.functions.isKeeper(keeper=address).call()

    def _transact(
        self, address: str, private_key: str, function: ContractFunction
    ) -> TxReceipt:
        """Perform transaction"""

        # get nonce
        nonce = Nonce(self.web3.eth.get_transaction_count(address))

        # acquire tx_parameters
        tx_parameters = TxParams()
        tx_parameters["from"] = address
        tx_parameters["nonce"] = nonce
        tx_parameters["gasPrice"] = Wei(int(self.web3.eth.gas_price * GAS_MULTIPLIER))
        _logger.info(f"tx_parameters = {tx_parameters}")

        # build tx
        tx = function.buildTransaction(tx_parameters)
        tx["gas"] = self.web3.eth.estimate_gas(tx)
        _logger.info(f"tx = {tx}")

        # sign transaction
        signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)
        _logger.info(f"signed_tx = {signed_tx}")

        # send transaction
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        _logger.info(f"tx_hash = {tx_hash.hex()}")

        # await transaction receipt
        tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        _logger.info(f"tx_receipt = {tx_receipt}")

        return tx_receipt

    def approve(self, address: str, private_key: str, amount: Wei) -> TxReceipt:
        """Allows a keeper to activate/register themselves after bonding."""

        function = self.functions.approve(spender=self.address, amount=amount)
        return self._transact(address, private_key, function)

    def bond(self, address: str, private_key: str, amount: Wei) -> TxReceipt:
        """Begin the bonding process for a new keeper. Default bonding period takes 3 days."""

        function = self.functions.bond(bonding=self.address, amount=amount)
        return self._transact(address, private_key, function)

    def activate(self, address: str, private_key: str) -> TxReceipt:
        """Allows a keeper to activate/register themselves after bonding."""

        function = self.functions.activate(bonding=self.address)
        return self._transact(address, private_key, function)

    def unbond(self, address: str, private_key: str, amount: int) -> TxReceipt:
        """Begin the unbonding process to stop being a keeper. Default unbonding period is 14 days."""

        function = self.functions.unbond(bonding=self.address, amount=amount)
        return self._transact(address, private_key, function)

    def withdraw(self, address: str, private_key: str, amount: int) -> TxReceipt:
        """Withdraw funds after unbonding has finished."""

        function = self.functions.withdraw(bonding=self.address, amount=amount)
        return self._transact(address, private_key, function)
