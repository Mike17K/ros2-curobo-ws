FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# ---- Base dependencies ----
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libacl1-dev \
    libncurses5-dev \
    pkg-config \
    maven \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# =========================================================
# 🔹 Build iceoryx (official way)
# =========================================================
RUN git clone https://github.com/eclipse-iceoryx/iceoryx.git

WORKDIR /opt/iceoryx

RUN cmake -B build -H iceoryx_meta \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_ALL=ON

RUN cmake --build build -j$(nproc)

RUN cmake --build build --target install

# =========================================================
# 🔹 Build Cyclone DDS WITH SHM support
# =========================================================
WORKDIR /opt

RUN git clone https://github.com/eclipse-cyclonedds/cyclonedds.git

WORKDIR /opt/cyclonedds

RUN cmake -B build \
    -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_EXAMPLES=ON \
    -DCMAKE_PREFIX_PATH=/usr/local

RUN cmake --build build -j$(nproc)

RUN cmake --build build --target install

# =========================================================
# 🔹 Runtime setup
# =========================================================
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
ENV CYCLONEDDS_URI=file:///cyclonedds.xml

# Copy configs
COPY cyclonedds.xml /cyclonedds.xml
COPY config/iox_config.toml /iox_config.toml

# Default: run RouDi
CMD ["iox-roudi", "-c", "/iox_config.toml"]