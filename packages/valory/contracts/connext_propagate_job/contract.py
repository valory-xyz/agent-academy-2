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
from typing import Any, Dict, List, Optional, Tuple, Type, cast

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.registries import ledger_apis_registry
from aea_ledger_ethereum import EthereumApi
from eth_typing import HexStr
from web3.types import RPCEndpoint


PUBLIC_ID = PublicId.from_str("valory/connext_propagate_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

ONE_ETH = 10**18
ZERO_ETH = 0
ETHEREUM_L1 = "ethereum"
ARBITRUM = "arbitrum"
ZKSYNC = "zksync"
REQUIRED_LEDGER_APIS = [
    ETHEREUM_L1,
    ARBITRUM,
    ZKSYNC,
]


@dataclass
class CallData:
    """A class to represent call data for a given connector."""

    encoded_data: bytes
    fee: int


class L2Network(ABC):
    """A class to represent a L2 network."""

    def __init__(self, ledger_apis: Dict[str, EthereumApi]) -> None:
        """Instantiate a L2 network."""
        self._ledger_apis = ledger_apis

    @property
    def l1(self) -> EthereumApi:
        """Get the L1 ledger api."""
        return self._ledger_apis[ETHEREUM_L1]

    @property
    def l2(self) -> EthereumApi:
        """Get the L2 ledger api."""
        raise NotImplementedError

    def _get_base_fee(self, ledger_api: EthereumApi) -> int:  # noqa
        """Return the base fee for the current block."""
        last_block = ledger_api.api.eth.get_block("latest")
        return last_block["baseFeePerGas"]

    def _get_gas_price(self, ledger_api: EthereumApi) -> int:  # noqa
        """Return the gas price for the current block."""
        gas_price = ledger_api.api.eth.gas_price
        return gas_price

    @abstractmethod
    def get_call_data(self) -> CallData:
        """Get the call data for an L2 network."""


class Arbitrum(L2Network):
    """A class that represents arbitrum."""

    gas_price_percent_increase = 2  # 200%
    submission_fee_percent_increase = 3  # 300%
    node_interface_address = "0x00000000000000000000000000000000000000C8"
    node_interface_abi = """[{
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
    arbitrum_hub_connector = "0xd151C9ef49cE2d30B829a98A07767E3280F70961"
    arbitrum_spoke_connector = "0xFD81392229b6252cF761459d370C239Be3aFc54F"
    spoke_connector_call_data = bytes.fromhex(
        "4ff746f6000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000001"
    )
    multiplier = 5

    @dataclass
    class L1ToL2Estimate:
        """A dataclass representing an L1->L2 message estimate."""

        gas_limit: int
        max_submission_fee: int
        max_fee_per_gas: int
        total_l2_gas_costs: int

    def __init__(self, ledger_apis: Dict[str, EthereumApi]):
        """Setup an arbitrum instance."""
        super().__init__(ledger_apis)
        self._node_interface_address = self.l1.api.toChecksumAddress(
            self.node_interface_address
        )
        self._node_interface_abi = json.loads(self.node_interface_abi)

    @property
    def l2(self) -> EthereumApi:
        """Get the L2 ledger api."""
        return self._ledger_apis[ARBITRUM]

    def estimate_submission_fee(
        self, data_length: int, base_fee: int
    ) -> int:  # pylint: disable=no-self-use; # noqa
        """
        Estimates the submission fee.

        Imitates the logic here (https://etherscan.io/address/0x5aed5f8a1e3607476f1f81c3d8fe126deb0afe94#code#F1#L361).
        :param data_length: the length of the data
        :param base_fee: the base fee
        :return: the submission fee
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
        contract = self.l2.api.eth.contract(
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
        l2_gas_price = self._get_gas_price(self.l2)
        max_fee_per_gas = l2_gas_price * (1 + self.gas_price_percent_increase)
        data_length = len(l2_call_data)
        submission_fee = self.estimate_submission_fee(data_length, l1_base_fee)
        max_submission_fee = submission_fee * (1 + self.submission_fee_percent_increase)
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

    def get_call_data(self) -> CallData:
        """Get call data for Arbitrum."""
        l1_base_fee = self._get_base_fee(self.l1)
        gas_price_bid = self._get_gas_price(self.l1)
        estimation = self.estimate_all(
            self.arbitrum_hub_connector,
            self.arbitrum_spoke_connector,
            self.spoke_connector_call_data,
            ZERO_ETH,
            l1_base_fee,
            self.arbitrum_spoke_connector,
            self.arbitrum_spoke_connector,
        )

        # multiply gas_limit by 5 to be successful in auto-redeem
        max_gas = estimation.gas_limit * self.multiplier
        submission_price_wei = estimation.max_submission_fee * self.multiplier
        fee = submission_price_wei + (max_gas * gas_price_bid)

        encoded_data = self.l2.api.codec.encode_abi(
            ["uint256", "uint256", "uint256"],
            [submission_price_wei, max_gas, gas_price_bid],
        )
        return CallData(
            encoded_data,
            fee,
        )


class ZkSync(L2Network):
    """ZkSync network."""

    gas_limit = 10_000_000
    gas_per_pubdata_byte = 800
    zksync_abi = [
        {
            "inputs": [
                {
                    "internalType": "uint256",
                    "name": "_gasPrice",
                    "type": "uint256",
                },
                {
                    "internalType": "uint256",
                    "name": "_l2GasLimit",
                    "type": "uint256",
                },
                {
                    "internalType": "uint256",
                    "name": "_l2GasPerPubdataByteLimit",
                    "type": "uint256",
                },
            ],
            "name": "l2TransactionBaseCost",
            "outputs": [
                {
                    "internalType": "uint256",
                    "name": "",
                    "type": "uint256",
                },
            ],
            "stateMutability": "view",
            "type": "function",
        },
    ]

    @property
    def l2(self) -> EthereumApi:
        """Get the L2 ledger api."""
        return self._ledger_apis[ZKSYNC]

    def _get_mainnet_contract_address(self) -> str:
        """Get ZkSync mainnet contract."""
        get_main_contract = RPCEndpoint("zks_getMainContract")
        res = self.l2.api.provider.make_request(get_main_contract, [])
        contract = res.get("result", None)
        if contract is None:
            raise ValueError("ZkSync mainnet contract not found.")
        return contract

    def _get_tx_cost_price(self) -> int:
        """Get the transaction cost price."""
        contract_address = self._get_mainnet_contract_address()
        contract = self.l1.api.eth.contract(
            address=self.l1.api.toChecksumAddress(contract_address),
            abi=self.zksync_abi,
        )
        l1_gas_price = self._get_gas_price(self.l1)
        tx_cost_price = contract.functions.l2TransactionBaseCost(
            l1_gas_price,
            self.gas_limit,
            self.gas_per_pubdata_byte,
        ).call()
        return tx_cost_price

    def get_call_data(self) -> CallData:
        """Get call data for ZkSync."""
        encoded_data = self.l1.api.codec.encode_abi(["uint256"], [self.gas_limit])
        fee = self._get_tx_cost_price()
        return CallData(
            encoded_data,
            fee,
        )


class Consensys(L2Network):
    """Consensys L2 network."""

    fee = 10**16  # 0.01ETH
    encoded_data = b""

    def get_call_data(self) -> CallData:
        """Get call data for Consensys."""
        return CallData(
            self.encoded_data,
            self.fee,
        )


class Bnb(L2Network):
    """BnB L2 network."""

    amb_address = "0xC10Ef9F491C9B59f936957026020C321651ac078"
    encoded_data = b""
    app_id = ""
    target_chain_id = 56
    data_length = 32
    amb_partial_abi = [
        {
            "inputs": [
                {"internalType": "string", "name": "_appID", "type": "string"},
                {"internalType": "uint256", "name": "_toChainID", "type": "uint256"},
                {"internalType": "uint256", "name": "_dataLength", "type": "uint256"},
            ],
            "name": "calcSrcFees",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function",
        }
    ]

    def _get_fee(self) -> int:
        """Get the transaction cost price."""
        amb_contract = self.l1.api.eth.contract(
            self.l1.api.toChecksumAddress(self.amb_address),
            abi=self.amb_partial_abi,
        )
        fee = amb_contract.functions.calcSrcFees(
            self.app_id, self.target_chain_id, self.data_length
        ).call()
        return fee

    def get_call_data(self) -> CallData:
        """Get call data for BnB."""
        fee = self._get_fee()
        return CallData(
            self.encoded_data,
            fee,
        )


class Gnosis(L2Network):
    """Gnosis L2 network."""

    fee = 0
    amb_address = "0x4C36d2919e407f0Cc2Ee3c993ccF8ac26d9CE64e"
    amb_partial_abi = [
        {
            "constant": True,
            "inputs": [],
            "name": "maxGasPerTx",
            "outputs": [{"name": "", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function",
        }
    ]
    encoded_data = b""

    def _get_fee(self) -> int:
        """Get the transaction cost price."""
        amb_contract = self.l1.api.eth.contract(
            self.l1.api.toChecksumAddress(self.amb_address),
            abi=self.amb_partial_abi,
        )
        fee = amb_contract.functions.maxGasPerTx().call()
        return fee

    def get_call_data(self) -> CallData:
        """Get call data for Gnosis."""
        fee = self._get_fee()
        encoded_data = self.l1.api.codec.encode_abi(["uint256"], [fee])
        return CallData(
            encoded_data,
            self.fee,
        )


GOERLI_CONFIG = [
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
        Consensys,
    ),
    (
        "0x80231092091d752e1506d4aab393675ebe388e9e",
        ZkSync,
    ),
    (
        "0x49174424e29950ad18d07b4d9ad2f77d0cbdda2a",
        None,
    ),
]
MAINNET_CONFIG = [
    ("0xfaf539a73659feaec96ec7242f075be0445526a8", Bnb),
    ("0x245F757d660C3ec65416168690431076d58d6413", Gnosis),
    ("0xd151c9ef49ce2d30b829a98a07767e3280f70961", Arbitrum),
    ("0xb01bc38909413f5dbb8f18a9b5787a62ce1282ae", None),
    ("0xf7c4d7dcec2c09a15f2db5831d6d25eaef0a296c", None),
]
MAINNET_ID = 1
GOERLI_ID = 5


CONNECTOR_CONFIGS: Dict[int, List[Tuple[str, Optional[Type[L2Network]]]]] = {
    MAINNET_ID: MAINNET_CONFIG,
    GOERLI_ID: GOERLI_CONFIG,
}


class ConnextPropagateJobContract(Contract):
    """Class for the ConnextPropagateJob contract."""

    contract_id = PUBLIC_ID

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
        return dict(set_ledger_api_configs=True)

    @staticmethod
    def _get_call_data(
        ledger_apis: Dict[str, EthereumApi],
        chain_id: int,
    ) -> Tuple[List[str], List[bytes], List[int]]:
        """Get the call data"""
        connector_config = CONNECTOR_CONFIGS[chain_id]
        connectors, encoded_data, fees = [], [], []
        for connector, l2_network in connector_config:
            single_encoded_data, fee = b"", 0
            if l2_network is not None:
                l2_network_instance = l2_network(ledger_apis)
                call_data = l2_network_instance.get_call_data()
                single_encoded_data = call_data.encoded_data
                fee = call_data.fee
            connectors.append(ledger_apis[ETHEREUM_L1].api.toChecksumAddress(connector))
            encoded_data.append(single_encoded_data)
            fees.append(fee)
        return connectors, encoded_data, fees

    @classmethod
    def _get_ledger_apis(
        cls, api_configs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, EthereumApi]:
        """Get the ledger APIs."""
        ledgers: Dict[str, EthereumApi] = {}
        for ledger_api_id in REQUIRED_LEDGER_APIS:
            if ledger_api_id not in api_configs:
                raise ValueError(f"Ledger API {ledger_api_id!r} not found in configs.")
            ledger_api = ledger_apis_registry.make(
                ETHEREUM_L1, **api_configs[ledger_api_id]
            )
            ledgers[ledger_api_id] = cast(EthereumApi, ledger_api)
        return ledgers

    @classmethod
    def workable(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the workable flag from the contract."""
        is_workable = False
        try:
            contract = cls.get_instance(ledger_api, contract_address)
            # static call to propagateWorkable()
            propagate_workable = contract.functions.propagateWorkable().call()
            if propagate_workable:
                data_str = cast(
                    HexStr,
                    cls.build_work_tx(ledger_api, contract_address, **kwargs)["data"],
                )[2:]
                # if the simulation succeeds, the job is workable
                is_workable = cls.simulate_tx(
                    ledger_api, contract_address, bytes.fromhex(data_str), **kwargs
                )["data"]
        except ValueError as e:
            _logger.info(f"propagateWorkable call failed: {str(e)}")
            is_workable = False
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
        ledger_api_configs = kwargs.get("ledger_api_configs", None)
        if ledger_api_configs is None:
            raise ValueError("'ledger_api_configs' is required.")
        ledger_apis = cls._get_ledger_apis(ledger_api_configs)
        chain_id = ledger_api.api.eth.chainId
        connectors, encoded_data, fees = cls._get_call_data(ledger_apis, chain_id)
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
        call_data = {
            "from": ledger_api.api.toChecksumAddress(keep3r_address),
            "to": ledger_api.api.toChecksumAddress(contract_address),
            "data": data.hex(),
        }
        try:
            ledger_api.api.eth.call(call_data)
            simulation_ok = True
        except ValueError as e:
            _logger.info(
                f"Simulation failed for tx with call data {call_data}: {str(e)}"
            )
            simulation_ok = False

        return dict(data=simulation_ok)
