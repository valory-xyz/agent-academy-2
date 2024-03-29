#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import pandas as pd
import requests
from web3 import Web3


# read API keys from environment
infura_api_key = os.environ.get("INFURA_API_KEY")  # pylint: disable=no-member
etherscan_api_key = os.environ.get("ETHERSCAN_API_KEY")  # pylint: disable=no-member
assert infura_api_key, "INFURA_API_KEY not found in environmental variables"
assert etherscan_api_key, "ETHERSCAN_API_KEY not found in environmental variables"


ENCODING = "utf-8"


KEEPER_API_URL = "https://keep3r.live/api/"
INFURA_TEMPLATE = "https://mainnet.infura.io/v3/{api_key}"
TEMPLATE_ABI_ENDPOINT = "https://api.etherscan.io/api?module=contract&action=getabi&address={address}&apikey={api_key}"
GITHUB_RAW_TEMPLATE = "https://raw.githubusercontent.com{suffix}"

# store data
PATH = (Path("tests").absolute() / "data" / "keep3r").absolute()
PATH.mkdir(parents=True, exist_ok=True)


w3 = Web3(Web3.HTTPProvider(INFURA_TEMPLATE.format(api_key=infura_api_key)))
assert w3.is_connected(), "Not connected"


def get_contract_abi(address: str) -> List[Dict[str, Any]]:
    """Get contract ABI from ethereum mainnet"""

    url = TEMPLATE_ABI_ENDPOINT.format(address=address, api_key=etherscan_api_key)
    response = requests.get(url)
    assert response.status_code == 200
    response_json = response.json()
    abi = json.loads(response_json["result"])
    return abi


def get_jobs_from_keep3r_live() -> pd.DataFrame:
    """Get jobs from keep3r.live"""

    response = requests.get(KEEPER_API_URL + "jobs")
    assert response.status_code == 200
    job_list = response.json()
    job_board = pd.DataFrame(job_list)
    return job_board


def get_readme_info(job: pd.Series) -> Optional[str]:
    """Get job documentation"""

    path = str(urlparse(job.docs).path)
    suffix = "/".join(filter(lambda x: x != "blob", path.split("/")))
    url = GITHUB_RAW_TEMPLATE.format(suffix=suffix)
    try:
        response = requests.get(url)
        assert response.status_code == 200
        documentation = response.content.decode(encoding=ENCODING)
        return documentation
    except Exception as e:  # pylint: disable=broad-except
        prefix = "Could not obtain documentation for"
        message = f"{prefix} {job.address}: {str(e)}"
        print(message)
    return None


def write_contract_data_to_local(contract_dir: Path, job: pd.Series) -> None:
    """Write contract data: ABI and README.md"""

    def write_abi() -> None:
        filepath = job_dir / "abi.json"
        abi = get_contract_abi(job.address)
        filepath.write_text(json.dumps(abi, indent=4))
        print(f"ABI written: {filepath}")

    def write_info() -> None:
        filepath = job_dir / "README.md"
        md = get_readme_info(job)
        if md is None:
            return
        filepath.write_text(md)
        print(f"documentation written: {filepath}")

    def write_details() -> None:
        filepath = job_dir / "contract_details.json"
        filepath.write_text(json.dumps(job.to_dict(), indent=4))
        print(f"details written: {filepath}")

    print(f"Scraping: {job.job_name}")
    job.address = Web3.to_checksum_address(job.address)
    job_dir = contract_dir / f"{job.address}"
    job_dir.mkdir(exist_ok=True)
    write_abi()
    write_info()
    write_details()


def get_keeper_contract_data() -> None:
    """Get keep3r job contract data"""

    job_board = get_jobs_from_keep3r_live()
    job_board.to_csv(PATH / "jobs.csv", index=False)
    contract_dir = PATH / "contracts"
    contract_dir.mkdir(exist_ok=True)
    for _, job in job_board.iterrows():  # job_name is not unique
        write_contract_data_to_local(contract_dir, job)
        time.sleep(0.1)
    print("Scraping contract ABIs completed")


def test_workable() -> None:
    """Test workable"""

    job_board = pd.read_csv(PATH / "jobs.csv")
    contract_dir = PATH / "contracts"
    for _, job in job_board.iterrows():
        checksum_address = Web3.to_checksum_address(job.address)
        filepath = Path(contract_dir / checksum_address / "abi.json")
        abi = json.loads(filepath.read_text(encoding=ENCODING))
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        try:
            result = contract.functions.workable().call()
            print(f"workable: {job.job_name}: {result}")
        except Exception as e:  # pylint: disable=broad-except
            print(f"cannot work: {job.job_name}: {str(e)}")


if __name__ == "__main__":
    get_keeper_contract_data()
    test_workable()
