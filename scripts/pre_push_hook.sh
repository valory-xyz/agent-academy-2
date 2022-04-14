#! /bin/bash
tox --parallel \
    -e pylint \
    -e mypy \
    -e flake8 \
    -e check-hash \
    -e isort \
    -e black \
    -e bandit && \
    echo "Done successfully!" && exit 0
echo "Failed!" && exit 1


