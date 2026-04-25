FROM nvcr.io/nvidia/pytorch:24.03-py3

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_DISTRO=humble
ENV DISPLAY=:0

# PATH updates
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

SHELL ["/bin/bash", "-c"]

RUN set -euo pipefail \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    locales \
    software-properties-common \
    curl \
    xdotool \
    xclip \
    gnupg2 \
    lsb-release \
    && locale-gen en_US en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && add-apt-repository -y universe \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -sc) main" | tee /etc/apt/sources.list.d/ros2.list > /dev/null \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    ros-humble-ros-base \
    ros-humble-rmw-cyclonedds-cpp \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-argcomplete \
    python3-venv \
    nano \
    terminator \
    # GUI & Tools
    ros-humble-rqt* \
    ros-humble-cv-bridge \
    # Camera & GStreamer
    ros-humble-gscam \
    ros-humble-v4l2-camera \
    ros-humble-image-pipeline \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-tools \
    libgstreamer1.0-dev \
    v4l-utils \
    # Navigation & Simulation
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-turtlebot3* \
    && rm -rf /var/lib/apt/lists/*

# Εγκατάσταση uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace

# Auto-source ROS και Setup
RUN echo "source /opt/ros/humble/setup.bash" >> /root/.bashrc \
    && echo 'if [ -f /workspace/install/setup.bash ]; then source /workspace/install/setup.bash; fi' >> /root/.bashrc \
    && echo 'if [ -f /workspace/.venv/bin/activate ]; then source /workspace/.venv/bin/activate; fi' >> /root/.bashrc
