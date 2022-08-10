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

"""This is a temporary script to write the missing data files on the autonomy framework installation"""

from autonomy.data import DATA_DIR


INSTALLATION_PATH = DATA_DIR.parent / "test_tools" / "data"

FILES = (
    (
        "encrypted_keys.json",
        """[
    {
        "address": "0xad00eD57566aff91A0e1CFc3C9233D0Ef2B761B1",
        "encrypted_key": "{\"address\": \"ad00ed57566aff91a0e1cfc3c9233d0ef2b761b1\", \"crypto\": {\"cipher\": \"aes-128-ctr\", \"cipherparams\": {\"iv\": \"2d8a75761e90aa1ee5f5a71c293af192\"}, \"ciphertext\": \"2b981a269476484b3fda873a7daa9a03b0def58c12b0b659d0770f46f3fea682\", \"kdf\": \"scrypt\", \"kdfparams\": {\"dklen\": 32, \"n\": 262144, \"r\": 1, \"p\": 8, \"salt\": \"492157cc06e5da254209e63907de2627\"}, \"mac\": \"c806509795e4bca29912e5914237d77fc1696dea8781eedcefc9e181d7f0db31\"}, \"id\": \"3ff66f96-1697-4723-8f1d-3a8cd4026015\", \"version\": 3}"
    },
    {
        "address": "0x709bDBE9289C0D7335691ba2Cf607Ba5F7F6F23b",
        "encrypted_key": "{\"address\": \"709bdbe9289c0d7335691ba2cf607ba5f7f6f23b\", \"crypto\": {\"cipher\": \"aes-128-ctr\", \"cipherparams\": {\"iv\": \"10c1f08cbb688a37b6cf1ab33b4b8f45\"}, \"ciphertext\": \"22d015a2cf5785fd0b3fd96ed5bfc3f22c62b6c8289e83f3843fc2d8caeba952\", \"kdf\": \"scrypt\", \"kdfparams\": {\"dklen\": 32, \"n\": 262144, \"r\": 1, \"p\": 8, \"salt\": \"1564601a38ab5f44502d01d4453eaed3\"}, \"mac\": \"ce358e4ecbf72fee0701a153784b46367935ae8aa79adfb9c1c1083be63d36d1\"}, \"id\": \"df71e851-42ba-48f6-aa74-5e5ea717b3e0\", \"version\": 3}"
    },
    {
        "address": "0x1398a5aDE9Cd3c293AD3b288f082C2BB8e12aB37",
        "encrypted_key": "{\"address\": \"1398a5ade9cd3c293ad3b288f082c2bb8e12ab37\", \"crypto\": {\"cipher\": \"aes-128-ctr\", \"cipherparams\": {\"iv\": \"ecad00ac0943a8c36529efb7c7b16d31\"}, \"ciphertext\": \"682f7f91c2116b36e65c0516d008577aaa9fc17b402017b14e0d9f74444df6c8\", \"kdf\": \"scrypt\", \"kdfparams\": {\"dklen\": 32, \"n\": 262144, \"r\": 1, \"p\": 8, \"salt\": \"33cb01b6ea17e65b051ea86d7611a79e\"}, \"mac\": \"928747a554bdd79acf4d19acca2cc66f3578edf4d46bf2e3279a18f222d3e5df\"}, \"id\": \"36c0f615-96d7-4f24-ab2e-a754ed927bb6\", \"version\": 3}"
    },
    {
        "address": "0x16d2E9FdbBdB87557FdF76Cd6A8587bE7925b2B0",
        "encrypted_key": "{\"address\": \"16d2e9fdbbdb87557fdf76cd6a8587be7925b2b0\", \"crypto\": {\"cipher\": \"aes-128-ctr\", \"cipherparams\": {\"iv\": \"650b297ff8e04ac534b63e1d8b9b8ffd\"}, \"ciphertext\": \"01e37219e59f00bd76bf26a945828e08ecdfa03d49f433b38e55934569027c41\", \"kdf\": \"scrypt\", \"kdfparams\": {\"dklen\": 32, \"n\": 262144, \"r\": 1, \"p\": 8, \"salt\": \"72bb12389bf56230a33c5e4fa0593675\"}, \"mac\": \"d43aaa336c5d9dab8705404dd9d33bde97fafe13a0a33328006964ca0c65e5b9\"}, \"id\": \"47b86216-dfbf-413b-aed4-df9ccdc02af7\", \"version\": 3}"
    }
]""",
    ),
    (
        "ethereum_key_1.txt",
        "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d",
    ),
    (
        "ethereum_key_2.txt",
        "0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a",
    ),
    (
        "ethereum_key_3.txt",
        "0x7c852118294e51e653712a81e05800f419141751be58f605c371e15141b007a6",
    ),
    (
        "ethereum_key_4.txt",
        "0x47e179ec197488593b187f80a00eb0da91f1b9d0b13f8733639f19c30a34926a",
    ),
    (
        "ethereum_key_deployer.txt",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    ),
)


def main() -> None:
    """Main function."""

    print(f"Installation path: {INSTALLATION_PATH}")
    for file, data in FILES:
        with open(INSTALLATION_PATH / file, "w+", newline="", encoding="utf-8") as fp:
            fp.write(data)


if __name__ == "__main__":
    main()
