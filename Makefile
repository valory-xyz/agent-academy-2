BLOCK_NUMBER ?= 11844372
MAINNET_KEY ?= ""
ROPSTEN_KEY ?= ""
ROPSTEN_DOCKER_PORT ?= 8545
MAINNET_DOCKER_PORT ?= 8546

.PHONY: clean
clean: clean-test clean-build clean-pyc clean-docs

.PHONY: clean-build
clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr pip-wheel-metadata
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -fr {} +
	find . -type d -name __pycache__ -exec rm -rv {} +
	rm -fr Pipfile.lock

.PHONY: clean-docs
clean-docs:
	rm -fr site/

.PHONY: clean-pyc
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.DS_Store' -exec rm -fr {} +

.PHONY: clean-test
clean-test:
	rm -fr .tox/
	rm -f .coverage
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;
	rm -fr coverage.xml
	rm -fr htmlcov/
	rm -fr .hypothesis
	rm -fr .pytest_cache
	rm -fr .mypy_cache/
	rm -fr .hypothesis/
	find . -name 'log.txt' -exec rm -fr {} +
	find . -name 'log.*.txt' -exec rm -fr {} +

# isort: fix import orders
# black: format files according to the pep standards
.PHONY: formatters
formatters:
	tomte format-code

# black-check: check code style
# isort-check: check for import order
# flake8: wrapper around various code checks, https://flake8.pycqa.org/en/latest/user/error-codes.html
# mypy: static type checker
# pylint: code analysis for code smells and refactoring suggestions
# darglint: docstring linter
.PHONY: code-checks
code-checks:
	tomte check-code

# safety: checks dependencies for known security vulnerabilities
# bandit: security linter
.PHONY: security
security:
	tomte check-security
	gitleaks detect --report-format json --report-path leak_report

# generate latest abci docstrings
# generate latest hashes for updated packages
# update copyright headers
.PHONY: generators
generators:
	tox -e abci-docstrings
	tomte format-copyright --author valory --exclude-part abci --exclude-part http_client --exclude-part ipfs --exclude-part p2p_libp2p_client --exclude-part gnosis_safe --exclude-part gnosis_safe_proxy_factory --exclude-part multisend --exclude-part service_registry --exclude-part acn --exclude-part contract_api --exclude-part http --exclude-part tendermint --exclude-part abstract_abci
	autonomy packages lock

.PHONY: common-checks-1
common-checks-1:
	tomte check-copyright --author valory --exclude-part abci --exclude-part http_client --exclude-part ipfs --exclude-part p2p_libp2p_client --exclude-part gnosis_safe --exclude-part gnosis_safe_proxy_factory --exclude-part multisend --exclude-part service_registry --exclude-part acn --exclude-part contract_api --exclude-part http --exclude-part tendermint --exclude-part abstract_abci
	tomte check-doc-links --url-skips https://eips.ethereum.org/EIPS/eip-1884[EIP1884] --url-skips "https://gasprice.poa.network/'" --url-skips https://diligence.consensys.net/posts/2019/09/stop-using-soliditys-transfer-now/[Learn
	tox -p -e check-hash -e check-packages

.PHONY: test
test:
	pytest -rfE tests/ --cov-report=html --cov=packages --cov-report=xml --cov-report=term --cov-report=term-missing --cov-config=.coveragerc
	find . -name ".coverage*" -not -name ".coveragerc" -exec rm -fr "{}" \;

v := $(shell pip -V | grep virtualenvs)

.PHONY: new_env
new_env: clean
	if [ ! -z "$(which svn)" ];\
	then\
		echo "The development setup requires SVN, exit";\
		exit 1;\
	fi;\

	if [ -z "$v" ];\
	then\
		pipenv --rm;\
		pipenv --clear;\
		pipenv --python 3.10;\
		pipenv install --dev --skip-lock;\
		echo "Enter virtual environment with all development dependencies now: 'pipenv shell'.";\
	else\
		echo "In a virtual environment! Exit first: 'exit'.";\
	fi

.PHONY: fix-abci-app-specs
fix-abci-app-specs:
	export PYTHONPATH=${PYTHONPATH}:${PWD} && autonomy analyse abci generate-app-specs packages.keep3r_co.skills.keep3r_job_abci.rounds.Keep3rJobAbciApp packages/keep3r_co/skills/keep3r_job/fsm_specification.yaml || (echo "Failed to check job abci consistency" && exit 1)
	export PYTHONPATH=${PYTHONPATH}:${PWD} && autonomy analyse abci generate-app-specs packages.keep3r_co.skills.keep3r_abci.composition.Keep3rAbciApp packages/keep3r_co/skills/keep3r_abci/fsm_specification.yaml || (echo "Failed to check chained abci cosistency" && exit 1)
	echo "Successfully validated abcis!"

.PHONY: run-mainnet-fork
run-mainnet-fork:
	@cd tests/helpers/hardhat;\
  	echo "Forking MainNet on block $(BLOCK_NUMBER)";\
	npx hardhat node --fork https://eth-mainnet.alchemyapi.io/v2/$(MAINNET_KEY) --fork-block-number $(BLOCK_NUMBER)

.PHONY: run-ropsten-fork
run-ropsten-fork:
	@cd tests/helpers/hardhat;\
  	echo "Forking Ropsten on block $(BLOCK_NUMBER)";\
	npx hardhat node --fork https://eth-ropsten.alchemyapi.io/v2/$(ROPSTEN_KEY) --fork-block-number $(BLOCK_NUMBER)

.PHONY: build-fork-image
build-fork-image:
	@echo "Building docker image for hardhat";\
	cd tests/helpers/hardhat;\
	docker build . -t hardhat:latest

.PHONY: run-ropsten-fork-docker
run-ropsten-fork-docker:
	@echo Running ropsten fork as a docker container;\
	docker run -d -e KEY=$(ROPSTEN_KEY) --name ropsten-fork -e NETWORK=ropsten -e BLOCK_NUMBER=$(BLOCK_NUMBER) -p $(ROPSTEN_DOCKER_PORT):8545 hardhat:latest

.PHONY: run-mainnet-fork-docker
run-mainnet-fork-docker:
	@echo Running mainnet fork as a docker container;\
	docker run -d -e KEY=$(MAINNET_KEY) --name mainnet-fork -e NETWORK=mainnet -e BLOCK_NUMBER=$(BLOCK_NUMBER) -p $(MAINNET_DOCKER_PORT):8545 hardhat:latest
