
# agent-academy-2

Valory's Agent Academy 2 - participant repo

- Clone the repository:

      git clone git@github.com:valory-xyz/agent-academy-4.git

- System requirements:

    - Python `>=3.7`
    - [Tendermint](https://docs.tendermint.com/master/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==0.6.0`
    - [Pipenv](https://pipenv.pypa.io/en/latest/install/) `>=2021.x.xx`
    - [Docker Engine](https://docs.docker.com/engine/install/)
    - [Docker Compose](https://docs.docker.com/compose/install/)

- Pull pre-built images:

      docker pull valory/autonolas-registries:latest
      docker pull valory/safe-contract-net:latest

- Create development environment:

      make new_env && pipenv shell

- Configure command line:

      autonomy init --reset --author academy2 --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"

- Pull packages:

      autonomy packages sync

- During development use `make formatters`, `make code-checks` and `make generators`


## Running the Keep3r

Create a virtual environment with all development dependencies:

```bash
make new_env
```

Enter virtual environment:

``` bash
pipenv shell
```

To run the end-to-end tests:

``` bash
pytest tests/test_agents/test_keep3r_bot_abci.py
```

which will run:
- `TestKeep3rABCISingleAgent`
- `TestKeep3rABCITwoAgents`
- `TestKeep3rABCIFourAgents`
