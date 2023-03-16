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
from typing import List, Tuple

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
    "bytecode": "0x608060405234801561001057600080fd5b5060405161072a38038061072a833981810160405281019061003291906104ae565b60008151905060008167ffffffffffffffff8111156100545761005361033f565b5b6040519080825280602002602001820160405280156100825781602001602082028036833780820191505090505b5090506000805b838110156101aa578573ffffffffffffffffffffffffffffffffffffffff16639f4713038683815181106100c0576100bf61050a565b5b60200260200101516040518263ffffffff1660e01b81526004016100e49190610548565b602060405180830381865afa158015610101573d6000803e3d6000fd5b505050506040513d601f19601f82011682018060405250810190610125919061059b565b1561019f5784818151811061013d5761013c61050a565b5b60200260200101518383815181106101585761015761050a565b5b602002602001019073ffffffffffffffffffffffffffffffffffffffff16908173ffffffffffffffffffffffffffffffffffffffff16815250508161019c90610601565b91505b806001019050610089565b5060008167ffffffffffffffff8111156101c7576101c661033f565b5b6040519080825280602002602001820160405280156101f55781602001602082028036833780820191505090505b50905060005b82811015610276578381815181106102165761021561050a565b5b60200260200101518282815181106102315761023061050a565b5b602002602001019073ffffffffffffffffffffffffffffffffffffffff16908173ffffffffffffffffffffffffffffffffffffffff16815250508060010190506101fb565b5060008160405160200161028a9190610707565b60405160208183030381529060405290506020810180590381f35b6000604051905090565b600080fd5b600080fd5b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b60006102e4826102b9565b9050919050565b60006102f6826102d9565b9050919050565b610306816102eb565b811461031157600080fd5b50565b600081519050610323816102fd565b92915050565b600080fd5b6000601f19601f8301169050919050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052604160045260246000fd5b6103778261032e565b810181811067ffffffffffffffff821117156103965761039561033f565b5b80604052505050565b60006103a96102a5565b90506103b5828261036e565b919050565b600067ffffffffffffffff8211156103d5576103d461033f565b5b602082029050602081019050919050565b600080fd5b6103f4816102d9565b81146103ff57600080fd5b50565b600081519050610411816103eb565b92915050565b600061042a610425846103ba565b61039f565b9050808382526020820190506020840283018581111561044d5761044c6103e6565b5b835b8181101561047657806104628882610402565b84526020840193505060208101905061044f565b5050509392505050565b600082601f83011261049557610494610329565b5b81516104a5848260208601610417565b91505092915050565b600080604083850312156104c5576104c46102af565b5b60006104d385828601610314565b925050602083015167ffffffffffffffff8111156104f4576104f36102b4565b5b61050085828601610480565b9150509250929050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052603260045260246000fd5b610542816102d9565b82525050565b600060208201905061055d6000830184610539565b92915050565b60008115159050919050565b61057881610563565b811461058357600080fd5b50565b6000815190506105958161056f565b92915050565b6000602082840312156105b1576105b06102af565b5b60006105bf84828501610586565b91505092915050565b7f4e487b7100000000000000000000000000000000000000000000000000000000600052601160045260246000fd5b6000819050919050565b600061060c826105f7565b91507fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff820361063e5761063d6105c8565b5b600182019050919050565b600081519050919050565b600082825260208201905092915050565b6000819050602082019050919050565b61067e816102d9565b82525050565b60006106908383610675565b60208301905092915050565b6000602082019050919050565b60006106b482610649565b6106be8185610654565b93506106c983610665565b8060005b838110156106fa5781516106e18882610684565b97506106ec8361069c565b9250506001810190506106cd565b5085935050505092915050565b6000602082019050818103600083015261072181846106a9565b90509291505056fe",
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

    @classmethod
    def workable(cls, ledger_api: EthereumApi, contract_address: str) -> JSONLike:
        """Check if there are any workable strategies."""
        strategies = cls.get_strategies(ledger_api)
        workable_strategies = cls.get_workable_strategies(
            ledger_api, contract_address, strategies
        )
        is_workable = len(workable_strategies) > 0
        return dict(data=is_workable)

    @classmethod
    def build_work_tx(  # pylint: disable=too-many-arguments,too-many-locals
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
    ) -> JSONLike:
        """
        Get the raw work transaction

        :param ledger_api: the ledger API object
        :param contract_address: the contract address

        :return: the raw transaction
        """
        contract = cls.get_instance(ledger_api, contract_address)
        strategies = cls.get_strategies(ledger_api)
        workable_strategies = cls.get_workable_strategies(
            ledger_api, contract_address, strategies
        )
        data = "0x"
        # it might happen that between the workable call,
        # and this one there are no more workable strategies
        if len(workable_strategies) > 0:
            data = contract.encodeABI(
                fn_name="work",
                args=[workable_strategies[0]],
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
        cls, ledger_api: EthereumApi, job_address: str, strategies: List[str]
    ) -> Tuple[str]:
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
        workable_strategies = ledger_api.api.codec.decode_abi(
            ["address[]"], encoded_strategies
        )
        # Return the workable strategies, the decoding returns a Tuple with a single element
        # so we need to access the first element of the tuple, which contains a tuple of workable strategies
        return workable_strategies[0]
