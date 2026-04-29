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
export LD_LIBRARY_PATH=/opt/hpcx/ucx/lib:/opt/hpcx/ucc/lib:$LD_LIBRARY_PATH
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp


sudo apt-get update && sudo apt-get install --reinstall -y \
  libmpich-dev \
  hwloc-nox libmpich12 mpich

echo "alias s='source ~/.bashrc && source .venv/bin/activate && source install/setup.bash'" >> ~/.bashrc
echo "alias r='bash scripts/launch.sh'" >> ~/.bashrc

echo "Setup complete."
