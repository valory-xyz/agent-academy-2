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

"""This module contains a class for the Phuture (Harvesting) Job contract."""

import logging
from typing import Any

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea_ledger_ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("valory/phuture_harvesting_job:0.1.0")

_logger = logging.getLogger(
    f"aea.packages.{PUBLIC_ID.author}.contracts.{PUBLIC_ID.name}.contract"
)

# USV_ADDRESS is the USDC vault address
USV_ADDRESS = "0x6bAD6A9BcFdA3fd60Da6834aCe5F93B8cFed9598"


class PhutureHarvestingJobContract(Contract):
    """Class for the PhutureJob contract."""

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
        return dict()

    @classmethod
    def _has_deposits(cls, ledger_api: EthereumApi, config_address: str) -> bool:
        """Check if there are depoists in the vault."""
        partial_abi = [
            {
                "inputs": [
                    {
                        "internalType": "address",
                        "name": "_savingsVault",
                        "type": "address",
                    }
                ],
                "name": "getDepositedAmount",
                "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function",
            }
        ]
        contract = ledger_api.api.eth.contract(
            address=ledger_api.api.to_checksum_address(config_address),
            abi=partial_abi,
        )
        deposit_amount = contract.functions.getDepositedAmount(USV_ADDRESS).call()
        return deposit_amount > 0

    @classmethod
    def workable(
        cls,
        ledger_api: EthereumApi,
        contract_address: str,
        **kwargs: Any,
    ) -> JSONLike:
        """Get the workable flag from the contract."""

        contract = cls.get_instance(ledger_api, contract_address)
        is_account_settlement_required = contract.functions.isAccountSettlementRequired(
            USV_ADDRESS
        ).call()
        job_config_address = contract.functions.jobConfig().call()
        can_harvest = contract.functions.canHarvest(
            USV_ADDRESS
        ).call() and cls._has_deposits(ledger_api, job_config_address)
        is_paused = contract.functions.paused().call()

        # the job is considered workable if account settlement is required or harvesting is possible and the job is not paused
        is_workable = (is_account_settlement_required or can_harvest) and not is_paused
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
        # we can either harvest or settle the account
        fn_name = "harvest"
        is_account_settlement_required = contract.functions.isAccountSettlementRequired(
            USV_ADDRESS
        ).call()
        if is_account_settlement_required:
            # if the account settlement is required, we settle the account
            # otherwise, we harvest
            fn_name = "settleAccount"

        data = contract.encodeABI(
            fn_name=fn_name,
            args=[USV_ADDRESS],
        )
        return dict(
            data=data,
        )

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
                    "from": ledger_api.api.to_checksum_address(keep3r_address),
                    "to": ledger_api.api.to_checksum_address(contract_address),
                    "data": data.hex(),
                }
            )
            simulation_ok = True
        except ValueError as e:
            _logger.info(f"Simulation failed: {str(e)}")
            simulation_ok = False

        return dict(data=simulation_ok)
