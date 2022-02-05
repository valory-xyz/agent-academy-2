
# agent-academy-2

Valory's Agent Academy 2 - participant repo

- Clone the repository, and recursively clone the submodules:

      git clone --recursive git@github.com:valory-xyz/agent-academy-2.git

  Note: to update the Git submodules later:

      git submodule update --init --recursive

## System requirements

- Python `>=3.7`
- Yarn `>=1.22.xx`
- Node `>=v12.xx`
- [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.11`
- [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
- [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`

Alternatively, you can fetch this docker image with the relevant requirments satisfied:

        docker pull valory/dev-template:latest
        docker container run -it valory/dev-template:latest

- Build the Hardhat projects:

      cd third_party/safe-contracts && yarn install
      cd ../..

## Simple ABCI example

Create a virtual environment with all development dependencies:

```bash
make new_env
```

Enter virtual environment:

``` bash
pipenv shell
```

To run the test:

``` bash
pytest tests/test_packages/test_agents/test_simple_abci.py::TestSimpleABCISingleAgent
```

or

``` bash
pytest tests/test_packages/test_agents/test_simple_abci.py::TestSimpleABCITwoAgents
```

or even

``` bash
pytest tests/test_packages/test_agents/test_simple_abci.py::TestSimpleABCIFourAgents
```

## Useful commands:

Check out the `Makefile` for useful commands, e.g. `make lint`, `make static` and `make pylint`, as well
as `make hashes`. To run all tests use `make test`.
