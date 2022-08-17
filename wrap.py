#!/usr/bin/env python3
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

"""This is a temporary wrapper of the autonomy CLI."""

import autonomy
from autonomy.data import DATA_DIR
from autonomy.cli.core import cli


CONFIG_PATH = DATA_DIR.parent / "configurations" / "schemas" / "service_schema.json"

CONFIG_FILE = """
{
  "$schema": "http://json-schema.org/draft-04/schema#",
  "description": "Schema for the deployment configuration file.",
  "additionalProperties": false,
  "type": "object",
  "required": [
    "name",
    "author",
    "version",
    "description",
    "aea_version",
    "license",
    "fingerprint",
    "fingerprint_ignore_patterns",
    "agent",
    "network",
    "number_of_agents"
  ],
  "properties": {
    "name": {
      "type": "string"
    },
    "author": {
      "type": "string"
    },
    "version": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "aea_version": {
      "type": "string"
    },
    "license": {
      "type": "string"
    },
    "fingerprint": {
      "type": "object"
    },
    "fingerprint_ignore_patterns": {
      "type": "array",
      "uniqueItems": true
    },
    "agent": {
      "type": "string"
    },
    "number_of_agents": {
      "type": "integer"
    },
    "network": {
      "enum": [
        "hardhat",
        "ropsten",
        "polygon",
        "goerli",
        "ethereum"
      ]
    }
  }
}
"""

ETHEREUM = {
    "LEDGER_ADDRESS": "https://mainnet.infura.io/v3/1622a5f5b56a4e1f9bd9292db7da93b8",
    "LEDGER_CHAIN_ID": 1,
}

if __name__ == "__main__":  # pragma: nocover
    with open(CONFIG_PATH, "w+", newline="", encoding="utf-8") as fp:
        fp.write(CONFIG_FILE)

    autonomy.deploy.constants.NETWORKS["docker-compose"]["ethereum"] = ETHEREUM
    autonomy.deploy.constants.NETWORKS["kubernetes"]["ethereum"] = ETHEREUM
    cli(prog_name="autonomy")  # type: ignore # pylint: disable = unexpected-keyword-arg, no-value-for-parameter
