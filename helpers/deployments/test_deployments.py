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

"""Tests package for the 'deployments' functionality."""
import os
import shutil
import tempfile
from abc import ABC
from glob import glob
from pathlib import Path
from typing import Any, List, Tuple

import yaml

from deployments.base_deployments import BaseDeployment, BaseDeploymentGenerator
from deployments.constants import DEPLOYMENT_SPEC_DIR, ROOT_DIR
from deployments.generators.docker_compose.docker_compose import DockerComposeGenerator
from deployments.generators.kubernetes.kubernetes import KubernetesGenerator


deployment_generators: List[Any] = [
    DockerComposeGenerator,
    KubernetesGenerator,
]

os.chdir(ROOT_DIR)

BASE_DEPLOYMENT: str = """name: "deployment_case"
author: "valory"
version: 0.1.0
agent: "valory/oracle_deployable:0.1.0"
network: hardhat
number_of_agents: 1
"""

LIST_SKILL_OVERRIDE: str = """public_id: valory/price_estimation_abci:0.1.0
type: skill
models:
  0:
    - price_api:
        args:
          url: 'https://api.coingecko.com/api/v3/simple/price'
          api_id: 'coingecko'
          parameters: '[["ids", "bitcoin"], ["vs_currencies", "usd"]]'
          response_key: 'bitcoin:usd'
          headers: ~
  1:
    - price_api:
        args:
          url: 'https://api.coingecko.com/api/v3/simple/price'
          api_id: 'coingecko'
          parameters: '[["ids", "bitcoin"], ["vs_currencies", "usd"]]'
          response_key: 'bitcoin:usd'
          headers: ~
"""
SKILL_OVERRIDE: str = """public_id: valory/price_estimation_abci:0.1.0
type: skill
models:
  price_api:
    args:
      url: ''
      api_id: ''
      headers: ''
      parameters: ''
      response_key: ''
  randomness_api:
    args:
      url: ""
      api_id: ""
"""
CONNECTION_OVERRIDE: str = """public_id: valory/ledger:0.1.0
type: connection
config:
  ledger_apis:
    ethereum:
      address: 'http://hardhat:8545'
      chain_id: '31337'
"""


TEST_DEPLOYMENT_PATH: str = "example-deployment.yaml"


def get_specified_deployments() -> List[str]:
    """Returns a list specified deployments."""
    return glob(str(DEPLOYMENT_SPEC_DIR / "*.yaml"))


def get_valid_deployments() -> List[str]:
    """Returns a list of valid deployments as string."""
    return [
        "---\n".join([BASE_DEPLOYMENT]),
        "---\n".join([BASE_DEPLOYMENT, CONNECTION_OVERRIDE]),
        "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE]),
        "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE, CONNECTION_OVERRIDE]),
    ]


class CleanDirectoryClass:
    """
    Loads the default aea into a clean temp directory and cleans up after.

    Used when testing code which leaves artifacts
    """

    working_dir: Path
    deployment_path = Path(ROOT_DIR) / "deployments"
    old_cwd = None

    def setup(self) -> None:
        """Sets up the working directory for the test method."""
        self.old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as path:
            self.working_dir = Path(path)
        shutil.copytree(self.deployment_path, self.working_dir)
        os.chdir(self.working_dir)

    def teardown(self) -> None:
        """Removes the over-ride"""
        shutil.rmtree(str(self.working_dir), ignore_errors=True)
        os.chdir(str(self.old_cwd))


class BaseDeploymentTests(ABC, CleanDirectoryClass):
    """Base pytest class for setting up Docker images."""

    deployment_spec_path: str

    @classmethod
    def setup_class(cls) -> None:
        """Setup up the test class."""

    @classmethod
    def teardown_class(cls) -> None:
        """Setup up the test class."""

    def write_deployment(
        self,
        app: str,
    ) -> str:
        """Write the deployment to the local directory."""
        with open(
            str(self.working_dir / TEST_DEPLOYMENT_PATH), "w", encoding="utf8"
        ) as f:
            f.write(app)
        return str(self.working_dir / TEST_DEPLOYMENT_PATH)

    @staticmethod
    def load_deployer_and_app(
        app: str, deployer: BaseDeploymentGenerator
    ) -> Tuple[BaseDeploymentGenerator, BaseDeployment]:
        """Handles loading the 2 required instances"""
        app_instance = BaseDeployment(path_to_deployment_spec=app)
        instance = deployer(deployment_spec=app_instance)  # type: ignore
        return instance, app_instance


class TestDockerComposeDeployment(BaseDeploymentTests):
    """Test class for DOcker-compose Deployment."""

    deployment_generator = DockerComposeGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        for spec in get_valid_deployments():
            if spec.find("ropsten") < 0:
                continue
            spec_path = self.write_deployment(spec)
            instance, app_instance = self.load_deployer_and_app(
                spec_path, self.deployment_generator  # type: ignore
            )
            output = instance.generate(app_instance)  # type: ignore
            containers = yaml.safe_load(output)["services"]
            assert "hardhat" not in containers.keys()


class TestKubernetesDeployment(BaseDeploymentTests):
    """Test class for Kubernetes Deployment."""

    deployment_generator = KubernetesGenerator

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""
        for spec in get_valid_deployments():
            if spec.find("ropsten") < 0:
                continue
            spec_path = self.write_deployment(spec)
            instance, app_instance = self.load_deployer_and_app(
                spec_path, self.deployment_generator  # type: ignore
            )
            output = instance.generate(app_instance)  # type: ignore
            resource_names = []
            for resource_yaml in yaml.safe_load_all(output):
                resource_names.append(resource_yaml["metadata"]["name"])
            assert "hardhat" not in resource_names


class TestDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_creates_hardhat_deploy(self) -> None:
        """Required for deployment of hardhat."""

    def test_creates_ropsten_deploy(self) -> None:
        """Required for deployment of ropsten."""

    def test_generates_agent_for_all_valory_apps(self) -> None:
        """Test generator functions with all valory apps."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agent(0)
                assert len(res) >= 1

    def test_generates_agents_for_all_valory_apps(self) -> None:
        """Test functionality of the valory deployment generators."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = app_instance.generate_agents()
                assert len(res) >= 1, "failed to generate agents"


class TestTendermintDeploymentGenerators(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_all_tendermint_configs(self) -> None:
        """Test functionality of the tendermint deployment generators."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                deployer_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                res = deployer_instance.generate_config_tendermint(app_instance)  # type: ignore
                assert len(res) >= 1, "Failed to generate Tendermint Config"


class TestDeploymentLoadsAgent(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_loads_agent_config(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                agent_json = app_instance.load_agent()
                assert agent_json != {}


class TestCliTool(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_deploy_safe_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_generates_deploy_oracle_contract(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec in get_valid_deployments():
                spec_path = self.write_deployment(spec)
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                if app_instance.network != "ropsten":
                    continue
                app_instance.generate_agent(0)


class TestValidates(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_generates_no_overrides(self) -> None:
        """Use a configuration with no overrides."""
        for deployment_generator in deployment_generators:
            spec_path = self.write_deployment(BASE_DEPLOYMENT)
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            agent_json = app_instance.load_agent()
            assert agent_json != {}

    def test_generates_with_one_override(self) -> None:
        """Use a configuration with no overrides."""
        for deployment_generator in deployment_generators[:]:
            spec_path = self.write_deployment(
                "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE])
            )
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            agent_json = app_instance.load_agent()
            assert agent_json != {}

    def test_fails_to_generate_with_to_many_overrides(self) -> None:
        """Use a configuration with no overrides."""
        for deployment_generator in deployment_generators:
            spec_path = self.write_deployment(
                "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE, SKILL_OVERRIDE])
            )
            try:
                self.load_deployer_and_app(spec_path, deployment_generator)
                raise AssertionError("Should not have generated deployment.")
            except ValueError:
                return

    def test_generates_all_specified_apps(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec_path in get_specified_deployments():
                _, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                app_instance.generate_agent(0)

    def test_generates_all_specified_deployments(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            for spec_path in get_specified_deployments():
                deployment_instance, app_instance = self.load_deployer_and_app(
                    spec_path, deployment_generator
                )
                deployment_instance.generate(app_instance)  # type: ignore


class TestOverrideTypes(BaseDeploymentTests):
    """Test functionality of the deployment generators."""

    def test_validates_with_singular_override(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            spec_path = self.write_deployment(
                "---\n".join([BASE_DEPLOYMENT, SKILL_OVERRIDE])
            )
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.validator.check_overrides_are_valid()

    def test_validates_with_list_override(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 2
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment), LIST_SKILL_OVERRIDE])
            )
            _, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.validator.check_overrides_are_valid()

    def test_validates_with_10_agents(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 10
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment)])
            )
            deployment_instance, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.validator.check_overrides_are_valid()
            app_instance.generate_agents()
            deployment_instance.generate(app_instance)  # type: ignore

    def test_validates_with_20_agents(self) -> None:
        """Test functionality of deploy safe contract."""
        for deployment_generator in deployment_generators:
            deployment = yaml.safe_load(BASE_DEPLOYMENT)
            deployment["number_of_agents"] = 20
            spec_path = self.write_deployment(
                "---\n".join([yaml.safe_dump(deployment)])
            )
            deployment_instance, app_instance = self.load_deployer_and_app(
                spec_path, deployment_generator
            )
            app_instance.validator.check_overrides_are_valid()
            app_instance.generate_agents()
            deployment_instance.generate(app_instance)  # type: ignore
