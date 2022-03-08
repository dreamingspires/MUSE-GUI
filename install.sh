#!/bin/sh
set -e
poetry install
poetry run python -m pip install git+ssh://git@github.com/SGIModel/MUSE_ICL.git
