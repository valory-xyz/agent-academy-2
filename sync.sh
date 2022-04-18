cp -r ../agent-academy-1/.github .
cp -r ../consensus-algorithms/packages/open_aea/protocols packages/open_aea
cp -r ../consensus-algorithms/packages/valory/agents/simple_abci packages/valory/agents
cp -r ../consensus-algorithms/packages/valory/agents/__init__.py packages/valory/agents
cp -r ../consensus-algorithms/packages/valory/connections/__init__.py packages/valory/connections
cp -r ../consensus-algorithms/packages/valory/connections/abci packages/valory/connections
cp -r ../consensus-algorithms/packages/valory/connections/http_client packages/valory/connections
cp -r ../consensus-algorithms/packages/valory/connections/ledger packages/valory/connections
cp -r ../consensus-algorithms/packages/valory/contracts/__init__.py packages/valory/contracts
cp -r ../consensus-algorithms/packages/valory/contracts/gnosis_safe packages/valory/contracts
cp -r ../consensus-algorithms/packages/valory/contracts/gnosis_safe_proxy_factory packages/valory/contracts
cp -r ../consensus-algorithms/packages/valory/protocols/__init__.py packages/valory/protocols
cp -r ../consensus-algorithms/packages/valory/protocols/abci packages/valory/protocols
cp -r ../consensus-algorithms/packages/valory/protocols/contract_api packages/valory/protocols
cp -r ../consensus-algorithms/packages/valory/protocols/http packages/valory/protocols
cp -r ../consensus-algorithms/packages/valory/protocols/ledger_api packages/valory/protocols
cp -r ../consensus-algorithms/packages/valory/skills/__init__.py packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/abstract_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/abstract_round_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/registration_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/reset_pause_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/safe_deployment_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/simple_abci packages/valory/skills
cp -r ../consensus-algorithms/packages/valory/skills/transaction_settlement_abci packages/valory/skills
cp -r ../consensus-algorithms/scripts/__init__.py scripts/
cp -r ../consensus-algorithms/scripts/check_copyright.py scripts/
cp -r ../consensus-algorithms/scripts/check_packages.py scripts/
cp -r ../consensus-algorithms/scripts/generate_abciapp_spec.py scripts/
cp -r ../consensus-algorithms/scripts/generate_ipfs_hashes.py scripts/
cp -r ../consensus-algorithms/tests/data tests
cp -r ../consensus-algorithms/tests/helpers/docker tests/helpers
cp -r ../consensus-algorithms/tests/helpers/__init__.py tests/helpers
cp -r ../consensus-algorithms/tests/helpers/async_utils.py tests/helpers
cp -r ../consensus-algorithms/tests/helpers/base.py tests/helpers
cp -r ../consensus-algorithms/tests/helpers/constants.py tests/helpers
cp -r ../consensus-algorithms/tests/helpers/contracts.py tests/helpers
cp -r ../consensus-algorithms/tests/helpers/tendermint_utils.py tests/helpers
cp -r ../consensus-algorithms/tests/test_agents/__init__.py tests/test_agents
#manual > cp -r ../consensus-algorithms/tests/test_agents/base.py tests/test_agents
#manual > cp -r ../consensus-algorithms/tests/test_agents/test_simple_abci.py tests/test_agents
cp -r ../consensus-algorithms/tests/test_contracts/test_gnosis_safe tests/test_contracts
cp -r ../consensus-algorithms/tests/test_contracts/test_gnosis_safe_proxy_factory tests/test_contracts
#manual > cp -r ../consensus-algorithms/tests/test_contracts/base.py tests/test_contracts
cp -r ../consensus-algorithms/tests/test_skills/__init__.py tests/test_skills
cp -r ../consensus-algorithms/tests/test_skills/test_simple_abci tests/test_skills
cp -r ../agent-academy-1/tox.ini .
echo "Manually sync: packages/valory/connections/abci, tests/helpers/docker, tests/test_agents/base.py, test_agents/test_simple_abci.py, tests/test_contracts/base.py"