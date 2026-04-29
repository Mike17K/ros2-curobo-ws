# !/bin/bash

sudo apt update
sudo apt install -y git wget python3-pip python3-colcon-common-extensions \
build-essential cmake
sudo apt install ros-humble-desktop
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
sudo apt install gz-harmonic
# check
gz sim

cd ~
git submodule add https://github.com/PX4/PX4-Autopilot.git external/PX4-Autopilot
cd external/PX4-Autopilot
git submodule update --init --recursive

# install dependencies
bash ./Tools/setup/ubuntu.sh


# run gazebo simulation
make px4_sitl gz_x500
make px4_sitl gz_quadrotor
make px4_sitl gz_standard_vtol