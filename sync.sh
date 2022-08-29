cp -r ../open-autonomy/packages/open_aea/protocols packages/open_aea
cp -r ../open-autonomy/packages/valory/connections/__init__.py packages/valory/connections
cp -r ../open-autonomy/packages/valory/connections/abci packages/valory/connections
cp -r ../open-autonomy/packages/valory/connections/http_client packages/valory/connections
cp -r ../open-autonomy/packages/valory/connections/ledger packages/valory/connections
cp -r ../open-autonomy/packages/valory/connections/p2p_libp2p_client packages/valory/connections
cp -r ../open-autonomy/packages/valory/contracts/__init__.py packages/valory/contracts
cp -r ../open-autonomy/packages/valory/contracts/gnosis_safe packages/valory/contracts
cp -r ../open-autonomy/packages/valory/contracts/gnosis_safe_proxy_factory packages/valory/contracts
cp -r ../open-autonomy/packages/valory/contracts/multisend packages/valory/contracts
cp -r ../open-autonomy/packages/valory/contracts/service_registry packages/valory/contracts
cp -r ../open-autonomy/packages/valory/protocols/__init__.py packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/abci packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/acn packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/contract_api packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/http packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/ledger_api packages/valory/protocols
cp -r ../open-autonomy/packages/valory/protocols/tendermint packages/valory/protocols
rm -rf packages/valory/skills
mkdir packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/__init__.py packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/abstract_abci packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/abstract_round_abci packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/registration_abci packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/reset_pause_abci packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/safe_deployment_abci packages/valory/skills
cp -r ../open-autonomy/packages/valory/skills/transaction_settlement_abci packages/valory/skills
cp -r ../open-autonomy/scripts/__init__.py scripts/
cp -r ../open-autonomy/scripts/check_copyright.py scripts/
cp -r ../open-autonomy/scripts/check_packages.py scripts/
cp -r ../open-autonomy/tests/test_agents/__init__.py tests/test_agents
cp -r ../open-autonomy/tests/test_skills/__init__.py tests/test_skills
cp -r ../agent-academy-1/.pylintrc .
cp -r ../agent-academy-1/Makefile .
cp -r ../agent-academy-1/pytest.ini .
cp -r ../agent-academy-1/setup.cfg .
cp -r ../agent-academy-1/tox.ini .

