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

"""Tests for the keep3r v1 contract."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, cast

from aea.common import JSONLike
from aea_ledger_ethereum import EthereumApi, EthereumCrypto
from web3 import HTTPProvider, Web3
from web3.types import Nonce, RPCEndpoint, TxParams, Wei

from autonomy.test_tools.base_test_classes.contracts import (
    BaseGanacheContractWithDependencyTest,
)
from autonomy.test_tools.docker.base import skip_docker_tests
from autonomy.test_tools.docker.ganache import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
)

from packages.valory.contracts.keep3r_test_job.contract import (
    PUBLIC_ID as TEST_JOB_PUBLIC_ID,
)
from packages.valory.contracts.keep3r_v1.contract import Keep3rV1Contract, PUBLIC_ID
from packages.valory.contracts.keep3r_v1_library.contract import (
    PUBLIC_ID as LIBRARY_PUBLIC_ID,
)

from tests.conftest import KEEP3R_V1_FOR_TEST, ROOT_DIR
from tests.test_contracts.constants import (
    DEFAULT_GAS,
    HALF_A_SECOND,
    ONE_ETH,
    SECONDS_PER_DAY,
)


BASE_CONTRACT_PATH = Path(ROOT_DIR, "packages", PUBLIC_ID.author, "contracts")
ENDPOINT_GANACHE_URI = f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}"


class BaseKeep3rV1ContractTest(BaseGanacheContractWithDependencyTest):
    """Base class for the Keep3rV1 contract tests"""

    contract_address = KEEP3R_V1_FOR_TEST
    contract_directory = BASE_CONTRACT_PATH / PUBLIC_ID.name

    ledger_api: EthereumApi
    ledger_identifier = EthereumCrypto.identifier

    dependencies = [
        (
            LIBRARY_PUBLIC_ID.name,
            Path(BASE_CONTRACT_PATH / LIBRARY_PUBLIC_ID.name),
            dict(gas=DEFAULT_GAS),
        ),
    ]

    ganache_provider = Web3(provider=HTTPProvider(ENDPOINT_GANACHE_URI)).provider

    @classmethod
    def mine_block(cls) -> None:
        """Force a block to be mined. Takes no parameters. Mines a block independent of whether or not mining is started or stopped."""

        endpoint = RPCEndpoint("evm_mine")
        cls.ganache_provider.make_request(endpoint, [])
        block_number = cls.ledger_api.api.eth.get_block_number()
        logging.info(f"Block {block_number} forcefully mined")

    @classmethod
    def time_jump(cls, seconds: int) -> None:
        """Jump forward in time. Takes one parameter, which is the amount of time to increase in seconds."""

        endpoint = RPCEndpoint("evm_increaseTime")
        response = cls.ganache_provider.make_request(endpoint, [seconds])
        logging.info(f"Time jumped to {response['result']} seconds")

    @classmethod
    def deployment_kwargs(cls) -> Dict[str, Any]:
        """Get deployment kwargs."""

        return dict(gas=DEFAULT_GAS, _kph=cls.deployer_crypto.address)

    @property
    def contract(self) -> Keep3rV1Contract:  # type: ignore
        """Get the contract."""

        return cast(Keep3rV1Contract, super().contract)

    @property
    def empty_address(self) -> str:
        """Empty wallet address"""

        return "0x1B621c19C3E868A4DF2E1858b08cedA8633927EA"

    @property
    def base_kw(self) -> Dict[str, str]:
        """Keyword arguments expected by every method call"""

        return dict(ledger_api=self.ledger_api, contract_address=self.contract_address)

    @staticmethod
    def get_tx_parameters(ledger_api: EthereumApi, address: str) -> TxParams:
        """Get transaction parameters."""

        tx_parameters = TxParams()
        nonce = Nonce(ledger_api.api.eth.get_transaction_count(address))
        tx_parameters["from"] = ledger_api.api.toChecksumAddress(address)
        tx_parameters["nonce"] = nonce
        tx_parameters["gas"] = Wei(DEFAULT_GAS)
        tx_parameters.update(ledger_api.try_get_gas_pricing())
        return tx_parameters

    @classmethod
    def perform_tx(cls, raw_tx: Dict[str, Any]) -> JSONLike:
        """Perform the transaction"""

        signed_tx = cls.deployer_crypto.sign_transaction(raw_tx)
        tx_digest = cls.ledger_api.send_signed_transaction(signed_tx)
        time.sleep(HALF_A_SECOND)
        cls.mine_block()
        tx_receipt = cls.ledger_api.get_transaction_receipt(tx_digest)
        time.sleep(HALF_A_SECOND)
        if not tx_receipt or not tx_receipt["status"]:
            raise ValueError(f"transaction failed: {tx_receipt}")
        return tx_receipt

    @classmethod
    def deploy_contract(cls, path: Path, **kwargs: Any) -> Any:
        """Deploy (additional) contract"""

        json_files = list(path.glob("build/*.json"))
        assert len(json_files) == 1, json_files
        interface = json.loads(json_files.pop().read_text(encoding="utf-8"))
        raw_tx = cls.ledger_api.get_deploy_transaction(
            interface, cls.deployer_crypto.address, **kwargs
        )
        tx_receipt = cls.perform_tx(raw_tx)
        contract_address = str(tx_receipt["contractAddress"])
        return cls.ledger_api.get_contract_instance(interface, contract_address)


@skip_docker_tests
class TestKeep3rV1Contract(BaseKeep3rV1ContractTest):
    """Test Keep3r V1 Contract"""

    def test_dependencies_deployed(self) -> None:
        """Test contract dependencies are successfully deployed"""

        assert self.dependency_info

    def test_contract_deployed(self) -> None:
        """Test contract is successfully deployed"""

        assert self.contract

    def test_get_jobs(self) -> None:
        """Test get_jobs"""

        assert self.contract.get_jobs(self.ledger_api, self.contract_address) == []

    def test_is_keeper(self) -> None:
        """Test is_keeper"""

        kw = dict(address=self.deployer_crypto.address)
        assert self.contract.is_keeper(**self.base_kw, **kw) is False

    def test_build_approve_tx(self) -> None:
        """Test get_jobs"""

        kw = dict(
            address=self.deployer_crypto.address,
            spender=self.empty_address,
            amount=ONE_ETH,
        )
        raw_tx = self.contract.build_approve_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0x095ea7b30000000000000000000000001b621c19c3e868a4df2e1858b08ceda8633927ea0000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_allowance(self) -> None:
        """Test allowance"""

        kw = dict(address=self.deployer_crypto.address, spender=self.empty_address)
        assert self.contract.allowance(**self.base_kw, **kw) == 0

    def test_build_bond_tx(self) -> None:
        """Test build_bond_tx"""

        kw = dict(address=self.empty_address, amount=ONE_ETH)
        raw_tx = self.contract.build_bond_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0xa515366a000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f05120000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_build_activate_tx(self) -> None:
        """Test build_activate_tx"""

        kw = dict(address=self.deployer_crypto.address)
        raw_tx = self.contract.build_activate_tx(**self.base_kw, **kw)
        expected = (
            "0x1c5a9d9c000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f0512"
        )
        assert raw_tx["data"] == expected

    def test_build_unbond_tx(self) -> None:
        """Test build_unbond_tx"""

        kw = dict(address=self.empty_address, amount=ONE_ETH)
        raw_tx = self.contract.build_unbond_tx(**self.base_kw, **kw)  # type: ignore
        expected = "0xa5d059ca000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f05120000000000000000000000000000000000000000000000000de0b6b3a7640000"
        assert raw_tx["data"] == expected

    def test_build_withdraw_tx(self) -> None:
        """Test build_withdraw_tx"""

        kw = dict(address=self.deployer_crypto.address)
        raw_tx = self.contract.build_withdraw_tx(**self.base_kw, **kw)
        expected = (
            "0x51cff8d9000000000000000000000000e7f1725e7734ce288f8367e1bb143e90bb3f0512"
        )
        assert raw_tx["data"] == expected


@skip_docker_tests
class TestKeep3rV1ContractWithTestJob(BaseKeep3rV1ContractTest):
    """Test Keep3r V1 Contract in conjunction with the TestJob contract."""

    job_path = Path(BASE_CONTRACT_PATH / TEST_JOB_PUBLIC_ID.name)
    test_job_contract: Any

    def add_job(self, contract_address: str) -> JSONLike:
        """Add job."""

        contract = self.contract.get_instance(**self.base_kw)  # type: ignore
        tx_parameters = self.get_tx_parameters(
            self.ledger_api, self.deployer_crypto.address
        )
        function = contract.functions.addJob(job=contract_address)
        raw_tx = function.buildTransaction(tx_parameters)
        return self.perform_tx(raw_tx)

    @classmethod
    def setup_class(cls) -> None:
        """Setup class"""

        super().setup_class()
        kwargs = dict(gas=DEFAULT_GAS, _keep3r=cls.deployer_crypto.address)
        cls.test_job_contract = cls.deploy_contract(cls.job_path, **kwargs)

    def test_keep3r_test_job_contract_deployed(self) -> None:
        """Test Keep3r TestJob contract is deployed"""

        assert self.test_job_contract

    def test_add_and_get_jobs(self) -> None:
        """Test get_jobs after adding the test job contract."""

        self.add_job(self.test_job_contract.address)
        expected = [self.test_job_contract.address]
        assert self.contract.get_jobs(**self.base_kw) == expected

    def test_become_keeper(self) -> None:
        """Test become keeper"""

        amount = 0
        kw = dict(address=self.deployer_crypto.address)
        assert self.contract.is_keeper(**self.base_kw, **kw) is False

        # 1. bond - normally has a bonding period associated
        raw_tx = self.contract.build_bond_tx(**self.base_kw, **kw, amount=amount)
        raw_tx["gas"] = DEFAULT_GAS
        self.perform_tx(raw_tx)

        # 2. wait bondTime - 3 days
        self.time_jump(3 * SECONDS_PER_DAY)

        # 3. activate
        raw_tx = self.contract.build_activate_tx(**self.base_kw, **kw)
        raw_tx["gas"] = DEFAULT_GAS
        self.perform_tx(raw_tx)

        # validate
        kw = dict(address=self.deployer_crypto.address)
        assert self.contract.is_keeper(**self.base_kw, **kw) is True
