# Χρησιμοποιούμε την εικόνα που είχατε πριν ως βάση
FROM nvcr.io/nvidia/pytorch:24.03-py3

# Αποφεύγουμε τα prompts κατά την εγκατάσταση
ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=humble
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

SHELL ["/bin/bash", "-c"]

# Εγκατάσταση ROS 2 Humble και βασικών εργαλείων από το setup script
RUN set -euo pipefail \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    locales \
    software-properties-common \
    curl \
    gnupg2 \
    lsb-release \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && add-apt-repository -y universe \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && UBUNTU_CODENAME="$(. /etc/os-release && echo "$UBUNTU_CODENAME")" \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu ${UBUNTU_CODENAME} main" \
    | tee /etc/apt/sources.list.d/ros2.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    ros-humble-ros-base \
    ros-humble-rmw-cyclonedds-cpp \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-argcomplete \
    python3-venv \
    nano \
    ros-humble-cv-bridge \
    ros-humble-rmw-fastrtps-cpp \
    # navigation stack dependencies
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    # optional: Gazebo for simulation
    ros-humble-gazebo-ros-pkgs \
    # optional for learning easy
    ros-humble-turtlebot3* terminator \
    && rm -rf /var/lib/apt/lists/*

# Εγκατάσταση uv (venv management)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Ρύθμιση Workspace
WORKDIR /workspace

# Ρύθμιση του entrypoint για να κάνει source το ROS αυτόματα
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc \
    && echo "if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi" >> /root/.bashrc
