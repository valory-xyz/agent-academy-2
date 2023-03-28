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

"""This module contains a class for the Yearn FactoryHarvestV1 Job contract."""

import logging
from typing import Any, List

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi
from web3.types import RPCEndpoint


PUBLIC_ID = PublicId.from_str("valory/yearn_factory_harvest_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

BATCH_WORKABLE_DATA = {
    "abi": [
        {
            "inputs": [
                {
                    "internalType": "contract IStrategyAggregator",
                    "name": "_strategyAggregator",
                    "type": "address",
                },
                {
                    "internalType": "address[]",
                    "name": "_strategies",
                    "type": "address[]",
                },
            ],
            "stateMutability": "nonpayable",
            "type": "constructor",
        }
    ],
    "bytecode": "0x608060405234801561001057600080fd5b5060405161072b38038061072b833981810160405281019061003291906104af565b60008151905060008167ffffffffffffffff81111561005457610053610340565b5b6040519080825280602002602001820160405280156100825781602001602082028036833780820191505090505b5090506000805b838110156101ab578573ffffffffffffffffffffffffffffffffffffffff16639f4713038683815181106100c0576100bf61050b565b5b60200260200101516040518263ffffffff1660e01b81526004016100e49190610549565b602060405180830381865afa92505050801561011e57506040513d601f19601f8201168201806040525081019061011b919061059c565b60015b156101a057801561019e5785828151811061013c5761013b61050b565b5b60200260200101518484815181106101575761015661050b565b5b602002602001019073ffffffffffffffffffffffffffffffffffffffff16908173ffffffffffffffffffffffffffffffffffffffff16815250508261019b90610602565b92505b505b806001019050610089565b5060008167ffffffffffffffff8111156101c8576101c7610340565b5b6040519080825280602002602001820160405280156101f65781602001602082028036833780820191505090505b50905060005b82811015610277578381815181106102175761021661050b565b5b60200260200101518282815181106102325761023161050b565b5b602002602001019073ffffffffffffffffffffffffffffffffffffffff16908173ffffffffffffffffffffffffffffffffffffffff16815250508060010190506101fc565b5060008160405160200161028b9190610708565b60405160208183030381529060405290506020810180590381f35b6000604051905090565b600080fd5b600080fd5b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b60006102e5826102ba565b9050919050565b60006102f7826102da565b9050919050565b610307816102ec565b811461031257600080fd5b50565b600081519050610324816102fe565b92915050565b600080fd5b6000601f19601f8301169050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fd5b6103788261032f565b810181811067ffffffffffffffff8211171561039757610396610340565b5b80604052505050565b60006103aa6102a6565b90506103b6828261036f565b919050565b600067ffffffffffffffff8211156103d6576103d5610340565b5b602082029050602081019050919050565b600080fd5b6103f5816102da565b811461040057600080fd5b50565b600081519050610412816103ec565b92915050565b600061042b610426846103bb565b6103a0565b9050808382526020820190506020840283018581111561044e5761044d6103e7565b5b835b8181101561047757806104638882610403565b845260208401935050602081019050610450565b5050509392505050565b600082601f8301126104965761049561032a565b5b81516104a6848260208601610418565b91505092915050565b600080604083850312156104c6576104c56102b0565b5b60006104d485828601610315565b925050602083015167ffffffffffffffff8111156104f5576104f46102b5565b5b61050185828601610481565b9150509250929050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052603260045260246000fd5b610543816102da565b82525050565b600060208201905061055e600083018461053a565b92915050565b60008115159050919050565b61057981610564565b811461058457600080fd5b50565b60008151905061059681610570565b92915050565b6000602082840312156105b2576105b16102b0565b5b60006105c084828501610587565b91505092915050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052601160045260246000fd5b6000819050919050565b600061060d826105f8565b91507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff820361063f5761063e6105c9565b5b600182019050919050565b600081519050919050565b600082825260208201905092915050565b6000819050602082019050919050565b61067f816102da565b82525050565b60006106918383610676565b60208301905092915050565b6000602082019050919050565b60006106b58261064a565b6106bf8185610655565b93506106ca83610666565b8060005b838110156106fb5781516106e28882610685565b97506106ed8361069d565b9250506001810190506106ce565b5085935050505092915050565b6000602082019050818103600083015261072281846106aa565b90509291505056fe",
}

VAULT_FACTORY_ADDRESS = "0x21b1FC8A52f179757bf555346130bF27c0C2A17A"
VAULT_FACTORY_DEPLOYMENT_BLOCK = "0xF76E83"
VAULT_ABI = '[{"inputs":[{"internalType":"address","name":"_registry","type":"address"},{"internalType":"address","name":"_convexStratImplementation","type":"address"},{"internalType":"address","name":"_curveStratImplementation","type":"address"},{"internalType":"address","name":"_convexFraxStratImplementation","type":"address"},{"internalType":"address","name":"_owner","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"category","type":"uint256"},{"indexed":true,"internalType":"address","name":"lpToken","type":"address"},{"indexed":false,"internalType":"address","name":"gauge","type":"address"},{"indexed":true,"internalType":"address","name":"vault","type":"address"},{"indexed":false,"internalType":"address","name":"convexStrategy","type":"address"},{"indexed":false,"internalType":"address","name":"curveStrategy","type":"address"},{"indexed":false,"internalType":"address","name":"convexFraxStrategy","type":"address"}],"name":"NewAutomatedVault","type":"event"},{"inputs":[],"name":"CATEGORY","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"CVX","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"acceptOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"allDeployedVaults","outputs":[{"internalType":"address[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"baseFeeOracle","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"booster","outputs":[{"internalType":"contract IBooster","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"}],"name":"canCreateVaultPermissionlessly","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"convexFraxPoolRegistry","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"convexFraxStratImplementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"convexPoolManager","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"convexStratImplementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"convexVoter","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"}],"name":"createNewVaultsAndStrategies","outputs":[{"internalType":"address","name":"vault","type":"address"},{"internalType":"address","name":"convexStrategy","type":"address"},{"internalType":"address","name":"curveStrategy","type":"address"},{"internalType":"address","name":"convexFraxStrategy","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"},{"internalType":"string","name":"_name","type":"string"},{"internalType":"string","name":"_symbol","type":"string"}],"name":"createNewVaultsAndStrategiesPermissioned","outputs":[{"internalType":"address","name":"vault","type":"address"},{"internalType":"address","name":"convexStrategy","type":"address"},{"internalType":"address","name":"curveStrategy","type":"address"},{"internalType":"address","name":"convexFraxStrategy","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"curveStratImplementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"curveVoter","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"deployedVaults","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"depositLimit","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"}],"name":"doesStrategyProxyHaveGauge","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"fraxBooster","outputs":[{"internalType":"contract IBooster","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"fraxVoter","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_convexPid","type":"uint256"}],"name":"getFraxInfo","outputs":[{"internalType":"bool","name":"hasFraxPool","type":"bool"},{"internalType":"uint256","name":"convexFraxPid","type":"uint256"},{"internalType":"address","name":"stakingAddress","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"}],"name":"getPid","outputs":[{"internalType":"uint256","name":"pid","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"getProxy","outputs":[{"internalType":"address","name":"proxy","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"governance","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"guardian","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"harvestProfitMaxInUsdc","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"harvestProfitMinInUsdc","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"healthCheck","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"keepCRV","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"keepCVX","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"keepFXS","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"keeper","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_gauge","type":"address"}],"name":"latestStandardVaultFromGauge","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"management","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"managementFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"numVaults","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"pendingOwner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"performanceFee","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"registry","outputs":[{"internalType":"contract IRegistry","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_baseFeeOracle","type":"address"}],"name":"setBaseFeeOracle","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_booster","type":"address"}],"name":"setBooster","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_convexFraxPoolRegistry","type":"address"}],"name":"setConvexFraxPoolRegistry","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_convexFraxStratImplementation","type":"address"}],"name":"setConvexFraxStratImplementation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_convexPoolManager","type":"address"}],"name":"setConvexPoolManager","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_convexStratImplementation","type":"address"}],"name":"setConvexStratImplementation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_curveStratImplementation","type":"address"}],"name":"setCurveStratImplementation","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_depositLimit","type":"uint256"}],"name":"setDepositLimit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_fraxBooster","type":"address"}],"name":"setFraxBooster","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_governance","type":"address"}],"name":"setGovernance","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_guardian","type":"address"}],"name":"setGuardian","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_harvestProfitMaxInUsdc","type":"uint256"}],"name":"setHarvestProfitMaxInUsdc","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_harvestProfitMinInUsdc","type":"uint256"}],"name":"setHarvestProfitMinInUsdc","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_health","type":"address"}],"name":"setHealthcheck","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_keepCRV","type":"uint256"},{"internalType":"address","name":"_curveVoter","type":"address"}],"name":"setKeepCRV","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_keepCVX","type":"uint256"},{"internalType":"address","name":"_convexVoter","type":"address"}],"name":"setKeepCVX","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_keepFXS","type":"uint256"},{"internalType":"address","name":"_fraxVoter","type":"address"}],"name":"setKeepFXS","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_keeper","type":"address"}],"name":"setKeeper","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_management","type":"address"}],"name":"setManagement","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_managementFee","type":"uint256"}],"name":"setManagementFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"newOwner","type":"address"}],"name":"setOwner","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_performanceFee","type":"uint256"}],"name":"setPerformanceFee","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_registry","type":"address"}],"name":"setRegistry","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_tradeFactory","type":"address"}],"name":"setTradeFactory","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_treasury","type":"address"}],"name":"setTreasury","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"tradeFactory","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"treasury","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"}]'

TOPIC_STRATEGY_ADDED = "0x5a6abd2af9fe6c0554fa08649e2d86e4393ff19dc304d072d38d295c9291d4dc"  # StrategyAdded(address,uint256,uint256,uint256,uint256)
TOPIC_STRATEGY_ADDED_TO_QUEUE = "0xa8727d412c6fa1e2497d6d6f275e2d9fe4d9318d5b793632e60ad9d38ee8f1fa"  # StrategyAddedToQueue(address)
TOPIC_STRATEGY_REMOVED_FROM_QUEUE = "0x8e1ec3c16d6a67ea8effe2ac7adef9c2de0bc0dc47c49cdf18f6a8b0048085be"  # StrategyRemovedFromQueue(address)
TOPIC_STRATEGY_MIGRATED = "0x100b69bb6b504e1252e36b375233158edee64d071b399e2f81473a695fd1b021"  # StrategyMigrated(address,address)
TOPIC_STRATEGY_REVOKED = "0x4201c688d84c01154d321afa0c72f1bffe9eef53005c9de9d035074e71e9b32a"  # StrategyRevoked(address)
TOPICS = [
    TOPIC_STRATEGY_ADDED,
    TOPIC_STRATEGY_ADDED_TO_QUEUE,
    TOPIC_STRATEGY_MIGRATED,
    TOPIC_STRATEGY_REMOVED_FROM_QUEUE,
    TOPIC_STRATEGY_REVOKED,
]


class YearnFactoryHarvestJobContract(Contract):
    """Class for the YearnFactoryHarvest contract."""

    contract_id = PUBLIC_ID

    def get_off_chain_data(
        self, ledger_api: EthereumApi, contract_address: str, **kwargs: Any
    ) -> JSONLike:
        """
        Get the off chain data from the contract.

        This contract doesn't have any off-chain data.

        :param ledger_api: the ledger API object
        :param contract_address: the contract address
        :param kwargs: other keyword arguments
        :return: the off chain data
        """
        return dict(chain_id="arbitrum")

    @classmethod
    def workable(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """Check if there are any workable strategies."""
        keep3r_address = kwargs.get("keep3r_address")
        strategies = cls.get_strategies(ledger_api)
        workable_strategies = cls.get_workable_strategies(
            ledger_api, contract_address, strategies, keep3r_address
        )
        is_workable = len(workable_strategies) > 0
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
        keep3r_address = kwargs.get("keep3r_address")
        strategies = cls.get_strategies(ledger_api)
        workable_strategies = cls.get_workable_strategies(
            ledger_api, contract_address, strategies, keep3r_address
        )
        data = "0x"
        # it might happen that between the workable call,
        # and this one there are no more workable strategies
        if len(workable_strategies) > 0:
            strategy = ledger_api.api.toChecksumAddress(workable_strategies[0])
            data = contract.encodeABI(
                fn_name="work",
                args=[strategy],
            )
        return dict(data=data)

    @classmethod
    def get_vaults(cls, ledger_api: EthereumApi) -> List[str]:
        """Get the vaults."""
        vault_address = ledger_api.api.toChecksumAddress(VAULT_FACTORY_ADDRESS)
        vault_factory = ledger_api.api.eth.contract(vault_address, abi=VAULT_ABI)
        all_vaults: List[str] = vault_factory.functions.allDeployedVaults().call()
        return all_vaults

    @classmethod
    def get_strategies(cls, ledger_api: EthereumApi) -> List[str]:
        """Get the strategies from all vaults."""
        all_vaults: List[str] = cls.get_vaults(ledger_api)
        logs_by_topic: dict = {}
        for topic in TOPICS:
            log_filter = {
                "address": all_vaults,
                "topics": [topic],
                "fromBlock": VAULT_FACTORY_DEPLOYMENT_BLOCK,
            }
            logs = ledger_api.api.provider.make_request(
                RPCEndpoint("eth_getLogs"), [log_filter]
            )
            logs_by_topic[topic] = logs["result"]

        strategy_added = [
            event["topics"][1] for event in logs_by_topic[TOPIC_STRATEGY_ADDED]
        ]
        strategy_added_to_queue = [
            event["topics"][1] for event in logs_by_topic[TOPIC_STRATEGY_ADDED_TO_QUEUE]
        ]
        strategy_migrated_from = [
            event["topics"][1] for event in logs_by_topic[TOPIC_STRATEGY_MIGRATED]
        ]
        strategy_migrated_to = [
            event["topics"][2] for event in logs_by_topic[TOPIC_STRATEGY_MIGRATED]
        ]
        strategy_removed_from_queue = [
            event["topics"][1]
            for event in logs_by_topic[TOPIC_STRATEGY_REMOVED_FROM_QUEUE]
        ]
        strategy_revoked = [
            event["topics"][1] for event in logs_by_topic[TOPIC_STRATEGY_REVOKED]
        ]

        all_added_strategies = (
            strategy_added + strategy_added_to_queue + strategy_migrated_to
        )
        all_removed_strategies = (
            strategy_migrated_from + strategy_removed_from_queue + strategy_revoked
        )
        available_strategies = set(all_added_strategies) - set(all_removed_strategies)

        # the strategies are provided to us as topics, we need to convert them to addresses
        available_strategy_addresses = [
            cls.address_from_topic(ledger_api, strategy)
            for strategy in available_strategies
        ]
        # sort the strategies to avoid mismatches in build_work_tx across agents
        available_strategy_addresses.sort()
        return available_strategy_addresses

    @staticmethod
    def address_from_topic(ledger_api: EthereumApi, topic: str) -> str:
        """Convert a topic to an address."""
        return ledger_api.api.toChecksumAddress("0x" + topic[26:256])

    @classmethod
    def get_workable_strategies(
        cls,
        ledger_api: EthereumApi,
        job_address: str,
        strategies: List[str],
        keep3r_address: str,
    ) -> List[str]:
        """Get the workable strategies."""
        # BatchWorkable contract is a special contract used specifically for checking if the strategies are workable
        # It is not deployed anywhere, nor it needs to be deployed
        batch_workable_contract = ledger_api.api.eth.contract(
            abi=BATCH_WORKABLE_DATA["abi"], bytecode=BATCH_WORKABLE_DATA["bytecode"]
        )

        # Encode the input data (constructor params)
        encoded_input_data = ledger_api.api.codec.encode_abi(
            ["address", "address[]"], [job_address, strategies]
        )

        # Concatenate the bytecode with the encoded input data to create the contract creation code
        contract_creation_code = batch_workable_contract.bytecode + encoded_input_data

        # Call the function with the contract creation code
        # Note that we are not sending any transaction, we are just calling the function
        # This is a special contract creation code that will return some result
        encoded_strategies = ledger_api.api.eth.call({"data": contract_creation_code})

        # Decode the response raw response
        # the decoding returns a Tuple with a single element so we need to access the first element of the tuple,
        # which contains a tuple of (possibly) workable strategies
        possibly_workable_strategies = ledger_api.api.codec.decode_abi(
            ["address[]"], encoded_strategies
        )[0]
        contract = cls.get_instance(ledger_api, job_address)

        # Check if the strategy is workable by making a static call
        # We need to do this because workable strategies can contain false positives
        def static_work(strategy: str) -> bool:
            """Check if the strategy is workable by making a static call."""
            try:
                contract.functions.work(
                    ledger_api.api.toChecksumAddress(strategy)
                ).call({"from": keep3r_address})
                # If the call succeeds, the strategy is workable
                return True
            except ValueError:
                # If the call fails, the strategy is not workable
                return False

        workable_strategies = [
            ledger_api.api.toChecksumAddress(strategy)
            for strategy in possibly_workable_strategies
            if static_work(strategy)
        ]
        return workable_strategies
