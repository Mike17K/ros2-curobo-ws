#!/bin/bash
set -euo pipefail

WS=$(pwd)

# shellcheck disable=SC1091
set +u
source /opt/ros/humble/setup.bash
set -u

if [ ! -d ".venv" ]; then
	uv venv --system-site-packages .venv
fi

uv sync

# shellcheck disable=SC1091
source .venv/bin/activate

export PYTHONPATH="${PYTHONPATH:-}:$WS/external"



echo "alias s='source .venv/bin/activate && source install/setup.bash'" >> ~/.bashrc

echo "Setup complete."
