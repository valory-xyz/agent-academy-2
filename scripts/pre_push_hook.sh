#! /bin/bash
# check abci consistency for the keeper job & abci app


make check_abci_specs || (echo "Failed to generated abci spec" && exit 1)

if [[ $(git diff --stat) != '' ]]; then
  echo 'working tree is dirty! Aborting..'  && exit 1
fi


tox --parallel \
    -e pylint \
    -e mypy \
    -e flake8 \
    -e check-hash \
    -e isort \
    -e isort-check \
    -e black \
    -e bandit && \
    echo "Done successfully!" && exit 0
echo "Failed!" && exit 1


