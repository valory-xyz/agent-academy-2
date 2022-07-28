#!/usr/bin/env python3
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

"""Scraping jobs from keep3r.live"""

import time
import os
import requests
import pandas as pd
import json
from urllib.parse import urlparse
from web3 import Web3
from pathlib import Path

# read API keys from environment
infura_api_key = os.environ.get("INFURA_API_KEY")
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")
assert infura_api_key, "INFURA_API_KEY not found in environmental variables"
assert etherscan_api_key, "ETHERSCAN_API_KEY not found in environmental variables"


ENCODING = "utf-8"


KEEPER_API_URL = "https://keep3r.live/api/"
INFURA_TEMPLATE = "https://mainnet.infura.io/v3/{api_key}"
TEMPLATE_ABI_ENDPOINT = "https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={api_key}"
GITHUB_RAW_TEMPLATE = "https://raw.githubusercontent.com{suffix}"

# store data
path = (Path("tests").absolute() / "data" / "keep3r").absolute()
path.mkdir(parents=True, exist_ok=True)


w3 = Web3(Web3.HTTPProvider(INFURA_TEMPLATE.format(api_key=infura_api_key)))
assert w3.isConnected(), "Not connected"


def get_contract_abi(address):
    """Get contract ABI from ethereum mainnet"""

    url = TEMPLATE_ABI_ENDPOINT.format(address=address, api_key=etherscan_api_key)
    response = requests.get(url)
    assert response.status_code == 200
    response_json = response.json()
    abi = json.loads(response_json['result'])
    return abi


def get_jobs_from_keep3r_live():
    """Get jobs from keep3r.live"""

    response = requests.get(KEEPER_API_URL + 'jobs')
    assert response.status_code == 200
    job_list = response.json()
    job_board = pd.DataFrame(job_list)
    return job_board


def get_readme_info(job):
    """Get job documentation"""

    path = str(urlparse(job.docs).path)
    suffix = "/".join(filter(lambda x: x != "blob", path.split("/")))
    url = GITHUB_RAW_TEMPLATE.format(suffix=suffix)
    try:
        response = requests.get(url)
        assert response.status_code == 200
        documentation = response.content.decode(encoding=ENCODING)
        return documentation
    except Exception as e:
        prefix = "Could not obtain documentation for"
        message = f"{prefix} {job.address}"
        print(message)


def write_contract_data_to_local(contract_dir, job):
    """Write contract data: ABI and README.md"""

    def write_abi():
        filepath = job_dir / "abi.json"
        abi = get_contract_abi(checksum_address)
        filepath.write_text(json.dumps(abi, indent=4))
        print(f"ABI written: {filepath}")

    def write_info():
        filepath = job_dir / "README.md"
        md = get_readme_info(job)
        if md is None:
            return
        filepath.write_text(md)
        print(f"documentation written: {filepath}")

    print(f"Scraping: {job.job_name}")
    checksum_address = Web3.toChecksumAddress(job.address)
    job_dir = contract_dir / f"{checksum_address}"
    job_dir.mkdir(exist_ok=True)
    write_abi()
    write_info()


def get_keeper_contract_data():
    """Get keep3r job contract data"""

    job_board = get_jobs_from_keep3r_live()
    job_board.to_csv(path / "jobs.csv", index=False)
    contract_dir = path / "contracts"
    contract_dir.mkdir(exist_ok=True)
    for _, job in job_board.iterrows():  # job_name is not unique
        write_contract_data_to_local(contract_dir, job)
        time.sleep(0.1)
    print("Scraping contract ABIs completed")


if __name__ == "__main__":
    get_keeper_contract_data()
