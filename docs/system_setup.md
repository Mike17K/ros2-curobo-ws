# Cuda drivers

```bash
nvidia-smi
nvcc --version
```

i have

nvcc: NVIDIA (R) Cuda compiler driver
Copyright (c) 2005-2023 NVIDIA Corporation
Built on Fri_Jan\_\_6_16:45:21_PST_2023
Cuda compilation tools, release 12.0, V12.0.140
Build cuda_12.0.r12.0/compiler.32267302_0

# Setup nvidia container toolkit

test

```
docker run --rm --gpus all nvidia/cuda:12.1.1-base-ubuntu22.04 nvidia-smi
```

if

docker: Error response from daemon: failed to discover GPU vendor from CDI: no known GPU vendor found

https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html

then

```bash
sudo apt-get update && sudo apt-get install -y --no-install-recommends \
   ca-certificates \
   curl \
   gnupg2

curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo sed -i -e '/experimental/ s/^#//g' /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update

export NVIDIA_CONTAINER_TOOLKIT_VERSION=1.19.0-1
  sudo apt-get install -y \
      nvidia-container-toolkit=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      nvidia-container-toolkit-base=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container-tools=${NVIDIA_CONTAINER_TOOLKIT_VERSION} \
      libnvidia-container1=${NVIDIA_CONTAINER_TOOLKIT_VERSION}


```

# Configure Docker

```
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

https://curobo.org/get_started/5_docker_development.html#docker-dev

Edit/create the /etc/docker/daemon.json with content:

```
    {
    "runtimes": {
        "nvidia": {
            "path": "/usr/bin/nvidia-container-runtime",
            "runtimeArgs": []
        }
    },
    "default-runtime": "nvidia" # ADD this line (the above lines will already exist in your json file)
    }
```

# Setup Steps

1. make sure VS Code extensions are installed for Dev Containers, ROS, Python, and C++
2. open docker/vision in a dev container (Ctrl + Shift + P -> Dev Containers: Open Folder in Container) or run docker compose from repo root
3. if post-create did not run, execute: bash /workspace/scripts/setup_workspace.sh (creates .venv via uv using .python-version)
4. run make inside /workspace (docker/vision)
