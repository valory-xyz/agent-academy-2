cp -r ../agent-academy-1/.github .
cp -r ../open-autonomy/packages/open_aea/ packages/
cp -r ../open-autonomy/packages/valory/ packages/
 cp -r ../open-autonomy/scripts/ .
cp -r ../open-autonomy/tests/data tests
cp -r ../open-autonomy/tests/helpers/docker tests/helpers
cp -r ../open-autonomy/tests/helpers/__init__.py tests/helpers
cp -r ../open-autonomy/tests/helpers/async_utils.py tests/helpers
cp -r ../open-autonomy/tests/helpers/base.py tests/helpers
# cp -r ../open-autonomy/tests/helpers/constants.py tests/helpers
cp -r ../open-autonomy/tests/helpers/contracts.py tests/helpers
cp -r ../open-autonomy/tests/helpers/tendermint_utils.py tests/helpers
cp -r ../open-autonomy/tests/test_agents/__init__.py tests/test_agents
cp -r ../open-autonomy/tests/test_agents/base.py tests/test_agents
cp -r ../open-autonomy/tests/test_agents/test_simple_abci.py tests/test_agents
cp -r ../open-autonomy/tests/test_contracts/base.py tests/test_contracts
cp -r ../open-autonomy/tests/test_skills/__init__.py tests/test_skills
#cp -r ../open-autonomy/tests/test_skills/test_simple_abci tests/test_skills
cp -r ../agent-academy-1/tox.ini .
echo "Manually sync: tests/helpers/constants.py, tests/test_skills/test_simple_abci"