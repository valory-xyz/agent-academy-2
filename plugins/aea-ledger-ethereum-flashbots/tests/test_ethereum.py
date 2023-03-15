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
# pylint: disable=redefined-outer-name,import-error,protected-access

"""Tests for the aea_ledger_ethereum_flashbots package."""

from unittest.mock import MagicMock, patch

import pytest
from aea.helpers.transaction.base import SignedTransaction
from aea_ledger_ethereum_flashbots.ethereum_flashbots import EthereumFlashbotApi
from eth_account import Account
from hexbytes import HexBytes
from web3.exceptions import TransactionNotFound
from web3.types import TxReceipt


@pytest.fixture
def ethereum_flashbot_api():
    """Get the ethereum flashbot API."""
    return EthereumFlashbotApi()


def test_init_with_signature_private_key():
    """Test init with signature private key."""
    signature_private_key = "my private key"
    with patch.object(
        Account, "from_key", side_effect=lambda private_key: MagicMock()
    ) as account_from_key_mock:
        EthereumFlashbotApi(signature_private_key=signature_private_key)
        assert account_from_key_mock.called_once_with(signature_private_key)


def test_init_without_signature_private_key():
    """Test init without signature private key."""
    with patch.object(
        Account, "create", side_effect=MagicMock()
    ) as account_create_mock:
        EthereumFlashbotApi()
        assert account_create_mock.called_once_with()


def test_bundle_transactions(ethereum_flashbot_api):
    """Test bundle transactions."""
    signed_transactions = [
        MagicMock(SignedTransaction, body=dict(raw_transaction="0x1234")),
    ]
    bundle = ethereum_flashbot_api.bundle_transactions(signed_transactions)
    assert len(bundle) == 1
    assert "signed_transaction" in bundle[0]
    assert bundle[0]["signed_transaction"] == HexBytes(
        signed_transactions[0].body["raw_transaction"]
    )


def test_simulate_with_successful_simulation(ethereum_flashbot_api):
    """Test simulate with successful simulation."""
    # mock
    response_mock = MagicMock()
    ethereum_flashbot_api._api.flashbots.simulate = MagicMock(
        return_value=response_mock
    )

    # run
    bundle = [{"signed_transaction": "0x1234"}]
    success = ethereum_flashbot_api.simulate(bundle, 123)

    # check
    ethereum_flashbot_api._api.flashbots.simulate.assert_called_once_with(bundle, 123)
    assert success


def test_simulate_with_failed_simulation(ethereum_flashbot_api):
    """Test simulate with failed simulation."""
    # mock
    response_mock = MagicMock(side_effect=Exception)
    ethereum_flashbot_api.api.flashbots.simulate = MagicMock(side_effect=response_mock)

    # run
    bundle = [{"signed_transaction": "0x1234"}]
    success = ethereum_flashbot_api.simulate(bundle, 123)

    # check
    ethereum_flashbot_api.api.flashbots.simulate.assert_called_once_with(bundle, 123)
    assert not success


def test_send_bundle_with_successful_transaction(ethereum_flashbot_api):
    """Test send bundle with successful transaction."""
    bundle = [{"signed_transaction": "0x1234", "hash": b"0x1234"}]
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.receipts = MagicMock(return_value=[TxReceipt(blockNumber=1)])
    response_mock.bundle = bundle
    ethereum_flashbot_api.api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.api.flashbots.send_bundle = MagicMock(
        return_value=response_mock
    )

    # run
    target_blocks = [123]
    tx_hashes = ethereum_flashbot_api.send_bundle(bundle, target_blocks)

    # check
    ethereum_flashbot_api.api.flashbots.simulate.assert_called_once_with(bundle, 123)
    ethereum_flashbot_api.api.flashbots.send_bundle.assert_called_once()
    assert response_mock.wait.called
    assert tx_hashes == [tx["hash"].hex() for tx in response_mock.bundle]


def test_bundle_transactions_with_empty_list(ethereum_flashbot_api):
    """Test bundle transactions with an empty list of signed transactions."""
    signed_transactions = []
    bundle = ethereum_flashbot_api.bundle_transactions(signed_transactions)
    assert len(bundle) == 0


def test_simulate_with_empty_bundle(ethereum_flashbot_api):
    """Test simulate with an empty bundle."""
    bundle = []
    success = ethereum_flashbot_api.simulate(bundle, 123)
    assert not success


def test_simulate_with_invalid_target_blocks(ethereum_flashbot_api):
    """Test simulate with invalid target blocks."""
    bundle = [{"signed_transaction": "0x1234"}]
    success = ethereum_flashbot_api.simulate(bundle, -1)
    assert not success


def test_bundle_and_send_with_successful_transaction(ethereum_flashbot_api):
    """Test bundle and send with successful transaction."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.receipts = MagicMock(
        return_value=[TxReceipt(blockNumber=1), TxReceipt(blockNumber=2)]
    )
    response_mock.bundle = [{"hash": b"0x1234"}, {"hash": b"0x5678"}]
    ethereum_flashbot_api.api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.api.flashbots.send_bundle = MagicMock(
        return_value=response_mock
    )

    # run
    signed_transactions = [
        MagicMock(SignedTransaction, body=dict(raw_transaction="0x1234")),
        MagicMock(SignedTransaction, body=dict(raw_transaction="0x5678")),
    ]
    target_blocks = [123]

    # check
    tx_hashes = ethereum_flashbot_api.bundle_and_send(
        signed_transactions, target_blocks
    )
    ethereum_flashbot_api.api.flashbots.simulate.assert_called_once()
    ethereum_flashbot_api.api.flashbots.send_bundle.assert_called_once()
    assert response_mock.wait.called
    assert tx_hashes == [tx["hash"].hex() for tx in response_mock.bundle]


def test_bundle_and_send_with_failed_simulation(ethereum_flashbot_api):
    """Test bundle and send with failed simulation."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api.api.flashbots.simulate = MagicMock(return_value=True)
    ethereum_flashbot_api.api.flashbots.send_bundle = MagicMock(
        return_value=response_mock
    )
    ethereum_flashbot_api.api.flashbots.cancel_bundles = MagicMock()
    ethereum_flashbot_api.api.toHex = MagicMock()
    ethereum_flashbot_api.api.flashbots.get_bundle_stats_v2 = MagicMock(
        return_value=response_mock
    )

    # run
    signed_transactions = [
        MagicMock(SignedTransaction, body=dict(raw_transaction="0x1234")),
        MagicMock(SignedTransaction, body=dict(raw_transaction="0x5678")),
    ]
    target_blocks = [123]
    tx_hashes = ethereum_flashbot_api.bundle_and_send(
        signed_transactions, target_blocks
    )

    # check
    ethereum_flashbot_api.api.flashbots.simulate.assert_called_once()
    ethereum_flashbot_api.api.flashbots.send_bundle.assert_called_once()
    ethereum_flashbot_api.api.flashbots.cancel_bundles.assert_called_once()
    assert tx_hashes is None


def test_send_bundle_with_failed_simulation(ethereum_flashbot_api):
    """Test send bundle with failed simulation."""
    # mock
    response_mock = MagicMock()
    response_mock.wait = MagicMock()
    response_mock.bundle_hash = MagicMock()
    response_mock.receipts = MagicMock(side_effect=TransactionNotFound)
    ethereum_flashbot_api.simulate = MagicMock(return_value=False)

    # run
    bundle = [{"signed_transaction": "0x1234", "hash": "0x1234"}]
    target_blocks = [123]
    tx_hashes = ethereum_flashbot_api.send_bundle(bundle, target_blocks)

    # check
    assert tx_hashes is None
