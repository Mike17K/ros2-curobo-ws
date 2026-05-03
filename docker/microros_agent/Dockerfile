# Χρησιμοποιούμε το επίσημο image της Jazzy ως βάση
FROM microros/micro-ros-agent:jazzy

# Εγκατάσταση του CycloneDDS RMW
RUN apt-get update && apt-get install -y \
    ros-jazzy-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

# Ορισμός του RMW σε CycloneDDS
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
