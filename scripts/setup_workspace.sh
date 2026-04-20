#!/bin/bash
set -e

# 1. Καθορισμός ROS Distro βάσει Ubuntu Version
UBUNTU_CODENAME=$(lsb_release -sc)
if [ "$UBUNTU_CODENAME" == "noble" ]; then
    ROS_DISTRO="jazzy"
elif [ "$UBUNTU_CODENAME" == "jammy" ]; then
    ROS_DISTRO="humble"
else
    ROS_DISTRO="jazzy" # Default για νεότερες εκδόσεις
fi

echo "Installing ROS 2 $ROS_DISTRO for Ubuntu $UBUNTU_CODENAME..."

# 2. Εγκατάσταση ROS 2
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt upgrade
# Desktop Install (Recommended)
sudo apt install ros-jazzy-desktop
source /opt/ros/jazzy/setup.bash

# 3. Εγκατάσταση Πακέτων (Χρησιμοποιώντας το $ROS_DISTRO)
sudo apt update
sudo apt install -y \
    git git-lfs build-essential cmake ninja-build python3-numpy \
    python3-colcon-common-extensions \
    ros-$ROS_DISTRO-desktop \
    ros-$ROS_DISTRO-camera-calibration-parsers \
    ros-$ROS_DISTRO-camera-info-manager \
    ros-$ROS_DISTRO-camera-calibration \
    ros-$ROS_DISTRO-image-pipeline \
    ros-$ROS_DISTRO-launch-testing-ament-cmake \
    libgtk2.0-dev pkg-config

# 4. Εγκατάσταση uv και ρύθμιση PATH αν δεν υπάρχει
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Προσθήκη στο .bashrc για μελλοντικά sessions
    grep -q ".cargo/bin" ~/.bashrc || echo 'export PATH="$PATH:$HOME/.cargo/bin"' >> ~/.bashrc
    
    # Ενημέρωση του PATH για το ΤΡΕΧΟΝ script execution
    export PATH="$PATH:$HOME/.cargo/bin"
else
    echo "uv is already installed."
fi

# 5. Aliases (Προσθήκη ελέγχου για αποφυγή διπλοεγγραφών)
grep -q "alias s=" ~/.bashrc || echo "alias s='source .venv/bin/activate && source install/setup.bash'" >> ~/.bashrc
grep -q "alias b=" ~/.bashrc || echo "alias b='source .venv/bin/activate && colcon build --symlink-install && source install/setup.bash'" >> ~/.bashrc

source ~/.bashrc

# 6. Git Config
git lfs install
git config --global --add safe.directory '*'
git config core.fileMode false
git config core.autocrlf input

# 7. Δημιουργία venv με system-site-packages
# Το --system-site-packages επιτρέπει στο venv να βλέπει τις βιβλιοθήκες του ROS (όπως το cv_bridge)
[ -d ".venv" ] || uv venv .venv --system-site-packages --python 3.12
source .venv/bin/activate
uv pip install -r requirements.txt

source .venv/bin/activate
export PYTHONPATH="$PYTHONPATH:$WS/external"

# configure docker size
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.rmem_default=2147483647
sudo sysctl -w net.core.wmem_max=2147483647
sudo sysctl -w net.core.wmem_default=2147483647

# optional cause we added volums to docker-compose.yaml
# xhost +local:root

echo "Setup complete!"
