# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""Keep3r network contracts image"""

import logging
import time
from typing import List

import docker
import requests
from docker.models.containers import Container

from autonomy.test_tools.docker.base import DockerImage
from autonomy.test_tools.docker.gnosis_safe_net import (
    DEFAULT_HARDHAT_ADDR,
    DEFAULT_HARDHAT_PORT,
)

from tests.helpers.constants import THIRD_PARTY_DIR


KEEP3R_V1_CONTRACT_DIR = THIRD_PARTY_DIR / "keep3r-v1-deploy"


class Keep3rNetDockerImage(DockerImage):
    """Spawn a local network with deployed Gnosis Safe Factory and Keep3rV1Contract contract"""

    def __init__(
        self,
        client: docker.DockerClient,
        addr: str = DEFAULT_HARDHAT_ADDR,
        port: int = DEFAULT_HARDHAT_PORT,
    ):
        """Initialize."""
        super().__init__(client)
        self.addr = addr
        self.port = port

    def create_many(self, nb_containers: int) -> List[Container]:
        """Instantiate the image in many containers, parametrized."""
        raise NotImplementedError()

    @property
    def tag(self) -> str:
        """Get the tag."""
        return "node:16.7.0"

    def _build_command(self) -> List[str]:
        """Build command."""
        return ["run", "hardhat", "extra-compile", "--port", str(self.port)]

    def create(self) -> Container:
        """Create the container."""
        cmd = self._build_command()
        working_dir = "/build"
        volumes = {
            str(KEEP3R_V1_CONTRACT_DIR): {
                "bind": working_dir,
                "mode": "rw",
            },
        }
        ports = {f"{self.port}/tcp": ("0.0.0.0", self.port)}  # nosec
        container = self._client.containers.run(
            self.tag,
            command=cmd,
            detach=True,
            ports=ports,
            volumes=volumes,
            working_dir=working_dir,
            entrypoint="yarn",
            extra_hosts={"host.docker.internal": "host-gateway"},
        )
        return container

    def wait(self, max_attempts: int = 15, sleep_rate: float = 1.0) -> bool:
        """
        Wait until the image is running.

        :param max_attempts: max number of attempts.
        :param sleep_rate: the amount of time to sleep between different requests.
        :return: True if the wait was successful, False otherwise.
        """
        for i in range(max_attempts):
            try:
                response = requests.get(f"{self.addr}:{self.port}")
                assert response.status_code == 200, ""
                return True
            except Exception as e:  # pylint: disable=broad-except
                logging.error("Exception: %s: %s", type(e).__name__, str(e))
                logging.info(
                    "Attempt %s failed. Retrying in %s seconds...", i, sleep_rate
                )
                time.sleep(sleep_rate)
        return False
