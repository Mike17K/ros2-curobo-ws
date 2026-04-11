#!/bin/bash
set -e

apt update
apt install -y curl gnupg lsb-release

curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add -
echo "deb http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list

apt update
apt install -y \
    git git-lfs build-essential cmake ninja-build python3-numpy \
    python3-colcon-common-extensions ros-humble-desktop
# camera deps
apt install -y ros-humble-camera-calibration-parsers ros-humble-camera-info-manager ros-humble-camera-calibration
# camera calibration deps
apt install -y ros-humble-image-pipeline
apt install ros-humble-launch-testing-ament-cmake
apt-get update && apt-get install -y libgtk2.0-dev pkg-config libgl1-mesa-glx



git lfs install

curl -LsSf https://astral.sh/uv/install.sh | sh
echo 'export PATH=$PATH:$HOME/.cargo/bin' >> /root/.bashrc

echo "alias s='source .venv/bin/activate && source install/setup.bash'" >> /root/.bashrc
echo "alias b='source .venv/bin/activate && make && source install/setup.bash'" >> /root/.bashrc

export PATH=$PATH:$HOME/.cargo/bin

# Αυτή η εντολή λέει στο Git να εμπιστεύεται κάθε φάκελο
git config --global --add safe.directory '*'
git config core.fileMode false
git config core.autocrlf input

source ~/.bashrc
uv venv --python 3.12 --system-site-packages .venv 