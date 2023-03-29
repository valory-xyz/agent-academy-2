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

"""This module contains a class for the ConnextPropagateJob contract."""
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional, List, Tuple, Type

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi

PUBLIC_ID = PublicId.from_str("valory/connext_propagate_goerli_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

ONE_ETH = 10**18
ZERO_ETH = 0


@dataclass
class CallData:
    encoded_data: bytes
    fee: int


class L2Network(ABC):
    """A class to represent a L2 network."""

    def __init__(self, ledger_api: EthereumApi) -> None:
        """Instantiate a L2 network."""
        self._ledger_api = ledger_api

    @abstractmethod
    def get_call_data(self, **kwargs: Any) -> CallData:
        """Get the call data for an L2 network."""


class Arbitrum(L2Network):
    """A class that represents arbitrum."""

    DEFAULT_GAS_PRICE_PERCENT_INCREASE = 2  # 200%
    DEFAULT_SUBMISSION_FEE_PERCENT_INCREASE = 3  # 300%
    NODE_INTERFACE_ADDRESS = "0x00000000000000000000000000000000000000C8"
    NODE_INTERFACE_ABI = """[{
          "inputs": [
             {
                "internalType":"address",
                "name":"sender",
                "type":"address"
             },
             {
                "internalType":"uint256",
                "name":"deposit",
                "type":"uint256"
             },
             {
                "internalType":"address",
                "name":"to",
                "type":"address"
             },
             {
                "internalType":"uint256",
                "name":"l2CallValue",
                "type":"uint256"
             },
             {
                "internalType":"address",
                "name":"excessFeeRefundAddress",
                "type":"address"
             },
             {
                "internalType":"address",
                "name":"callValueRefundAddress",
                "type":"address"
             },
             {
                "internalType":"bytes",
                "name":"data",
                "type":"bytes"
             }
          ],
          "name":"estimateRetryableTicket",
          "outputs":[],
          "stateMutability":"nonpayable",
          "type":"function"
       }]"""
    ARBITRUM_HUB_CONNECTOR = "0xd151C9ef49cE2d30B829a98A07767E3280F70961"
    ARBITRUM_SPOKE_CONNECTOR = "0xFD81392229b6252cF761459d370C239Be3aFc54F"
    SPOKE_CONNECTOR_CALL_DATA = bytes.fromhex(
        "4ff746f6000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001"
    )
    MULTIPLIER = 5

    @dataclass
    class L1ToL2Estimate:
        """A dataclass representing an L1->L2 message estimate."""

        gas_limit: int
        max_submission_fee: int
        max_fee_per_gas: int
        total_l2_gas_costs: int

    def __init__(self, ledger_api: EthereumApi):
        """Setup an arbitrum instance."""
        super().__init__(ledger_api)
        self._node_interface_address = self._ledger_api.api.toChecksumAddress(
            self.NODE_INTERFACE_ADDRESS
        )
        self._node_interface_abi = json.loads(self.NODE_INTERFACE_ABI)

    def l2_get_gas_price(self) -> int:
        """Returns the l2 gas price"""
        return self._ledger_api.api.eth.gas_price

    def estimate_submission_fee(
        self, data_length: int, base_fee: int
    ) -> int:  # pylint: disable=no-self-use; # noqa
        """
        Estimates the submission fee.

        Imitates the logic here (https://etherscan.io/address/0x5aed5f8a1e3607476f1f81c3d8fe126deb0afe94#code#F1#L361).
        """
        return (1400 + 6 * data_length) * base_fee

    def estimate_retryable_ticket_gas_limit(
        self,
        sender: str,
        destination: str,
        l2_call_value: int,
        excess_fee_refund_address: str,
        call_value_refund_address: str,
        calldata: bytes,
    ) -> int:
        """
        Estimate the amount of L2 gas required for putting the transaction in the L2 inbox, and executing it.

        Note: This method should be called against Arbitrum, i.e. ledger_api needs to point to arbitrum.

        :param sender: the sender of the L2 transaction
        :param destination: target
        :param l2_call_value: the amount to transfer
        :param excess_fee_refund_address: where to send the refund of fees
        :param call_value_refund_address: where to send the refund of call value
        :param calldata: the data to be estimated.
        :returns: the gas limit
        """
        sender_deposit = ONE_ETH + l2_call_value
        contract = self._ledger_api.api.eth.contract(
            self._node_interface_address, abi=self._node_interface_abi
        )
        estimated_gas = contract.functions.estimateRetryableTicket(
            sender,
            sender_deposit,
            destination,
            l2_call_value,
            excess_fee_refund_address,
            call_value_refund_address,
            calldata,
        ).estimateGas()
        return estimated_gas

    def estimate_all(
        self,
        sender: str,
        l2_call_to: str,
        l2_call_data: bytes,
        l2_call_value: int,
        l1_base_fee: int,
        excess_fee_refund_address: str,
        call_value_refund_address: str,
    ) -> L1ToL2Estimate:
        """
        Get gas limit, gas price and submission price estimates for sending an L1->L2 message.

        :param sender: Sender of the L1 to L2 transaction
        :param l2_call_to: Destination L2 contract address
        :param l2_call_data: The hex call data to be sent in the request
        :param l2_call_value: The value to be sent on L2 as part of the L2 transaction
        :param l1_base_fee: Current l1 base fee
        :param excess_fee_refund_address: The address to send excess fee refunds too
        :param call_value_refund_address: The address to send the call value
        :returns: the estimates for an L1->L2 message.
        """
        l2_gas_price = self.l2_get_gas_price()
        max_fee_per_gas = l2_gas_price * (1 + self.DEFAULT_GAS_PRICE_PERCENT_INCREASE)
        data_length = len(l2_call_data)
        submission_fee = self.estimate_submission_fee(data_length, l1_base_fee)
        max_submission_fee = submission_fee * (
            1 + self.DEFAULT_SUBMISSION_FEE_PERCENT_INCREASE
        )
        gas_limit = self.estimate_retryable_ticket_gas_limit(
            sender,
            l2_call_to,
            l2_call_value,
            excess_fee_refund_address,
            call_value_refund_address,
            l2_call_data,
        )
        total_l2_gas_costs = max_submission_fee + (gas_limit * max_fee_per_gas)
        return self.L1ToL2Estimate(
            gas_limit,
            max_submission_fee,
            max_fee_per_gas,
            total_l2_gas_costs,
        )

    def get_call_data(self, **kwargs: Any) -> CallData:
        """Get call data for Arbitrum."""
        l1_base_fee = kwargs.get("l1_base_fee", None)
        gas_price_bid = kwargs.get("gas_price_bid", None)
        if l1_base_fee is None or gas_price_bid is None:
            raise ValueError(
                "'l1_base_fee' and 'gas_price_bid' are required for Arbitrum."
            )
        estimation = self.estimate_all(
            self.ARBITRUM_HUB_CONNECTOR,
            self.ARBITRUM_SPOKE_CONNECTOR,
            self.SPOKE_CONNECTOR_CALL_DATA,
            ZERO_ETH,
            l1_base_fee,
            self.ARBITRUM_SPOKE_CONNECTOR,
            self.ARBITRUM_SPOKE_CONNECTOR,
        )

        # multiply gas_limit by 5 to be successful in auto-redeem
        max_gas = estimation.gas_limit * self.MULTIPLIER
        submission_price_wei = estimation.max_submission_fee * self.MULTIPLIER
        fee = submission_price_wei + (max_gas * gas_price_bid)

        encoded_data = self._ledger_api.api.codec.encode_abi(
            ["uint256", "uint256", "uint256"],
            [submission_price_wei, max_gas, gas_price_bid],
        )
        return CallData(
            encoded_data,
            fee,
        )


CHAIN_ID = "arbitrum"
CONNECTOR_ADDRESS_TO_L2: List[Tuple[str, Optional[Type[L2Network]]]] = [
    (
        "0xd045f03686575f042b21d0b3d20ffae4d3a3482f",
        None,
    ),
    (
        "0x9060e2b92a4e8d4ead05b7f3d736e3da33955fa5",
        None,
    ),
    (
        "0xe9c7095c956f9f75e21dd99027adf6bfffa9ba9a",
        None,
    ),
    (
        "0x58d3464e5aab9c598a7059d182720a04ad59b01f",
        Arbitrum,
    ),
    (
        "0x9f02b394d8f0e2df3f6913f375cd1f919c03987d",
        None,
    ),
    (
        "0x80231092091d752e1506d4aab393675ebe388e9e",
        None,
    ),
    (
        "0x49174424e29950ad18d07b4d9ad2f77d0cbdda2a",
        None,
    ),
]


class ConnextPropagateJobContract(Contract):
    """Class for the ConnextPropagateJob contract."""

    contract_id = PUBLIC_ID

    def _get_base_fee(self, ledger_api: EthereumApi) -> int:  # noqa
        """Return the base fee for the current block."""
        last_block = ledger_api.api.eth.get_block("latest")
        return last_block["baseFeePerGas"]

    def _get_gas_price(self, ledger_api: EthereumApi) -> int:  # noqa
        """Return the gas price for the current block."""
        gas_price = ledger_api.api.eth.gas_price
        return gas_price

    def get_off_chain_data(
        self, ledger_api: EthereumApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Get the off chain data from the contract.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param kwargs: other keyword arguments
        :return: the off chain data
        """
        base_fee = self._get_base_fee(ledger_api)
        gas_price = self._get_gas_price(ledger_api)
        return dict(
            chain_id=CHAIN_ID,
            l1_base_fee=base_fee,
            gas_price_bid=gas_price,
        )

    @staticmethod
    def _get_call_data(
        ledger_api: EthereumApi, **kwargs: Any
    ) -> Tuple[List[str], List[bytes], List[int]]:
        """Get the call data"""
        connectors, encoded_data, fees = [], [], []
        for connector, l2_network in CONNECTOR_ADDRESS_TO_L2:
            single_encoded_data, fee = b"0x", 0
            if l2_network is not None:
                l2_network_instance = l2_network(ledger_api)
                call_data = l2_network_instance.get_call_data(**kwargs)
                single_encoded_data = call_data.encoded_data
                fee = call_data.fee
            connectors.append(ledger_api.api.toChecksumAddress(connector))
            encoded_data.append(single_encoded_data)
            fees.append(fee)
        return connectors, encoded_data, fees

    @classmethod
    def workable(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the workable flag from the contract."""
        # this job is always assumed workable
        # whether its actually workable or not is determined by the simulation
        is_workable = True
        return dict(data=is_workable)

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
        connectors, encoded_data, fees = cls._get_call_data(ledger_api, **kwargs)
        data = contract.encodeABI(
            fn_name="propagateKeep3r",
            args=[connectors, fees, encoded_data],
        )
        return dict(data=data)

    @classmethod
    def simulate_tx(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        data: bytes,
        **kwargs: Any,
    ) -> JSONLike:
        """Simulate the transaction."""
        keep3r_address = kwargs.get("keep3r_address", None)
        if keep3r_address is None:
            raise ValueError("'keep3r_address' is required.")
        try:
            ledger_api.api.eth.call(
                {
                    "from": ledger_api.api.toChecksumAddress(keep3r_address),
                    "to": ledger_api.api.toChecksumAddress(contract_address),
                    "data": data.hex(),
                }
            )
            simulation_ok = True
        except ValueError as e:
            _logger.info(f"Simulation failed: {str(e)}")
            simulation_ok = False

        return dict(data=simulation_ok)
