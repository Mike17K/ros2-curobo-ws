#!/bin/bash
set -e

# --- 0. Ρυθμίσεις Διαδρομών ---
WS=$(pwd) # Ορίζει το workspace στον τρέχοντα φάκελο

FORCE=0
for arg in "$@"; do
    case "$arg" in
        --force)
            FORCE=1
            ;;
    esac
done

has_apt_pkg() {
    dpkg -s "$1" &> /dev/null
}

hash_file() {
    if command -v sha256sum &> /dev/null; then
        sha256sum "$1" | awk '{print $1}'
    else
        md5sum "$1" | awk '{print $1}'
    fi
}

# Ορισμός ROS Distro (τα images της OSRF μπορεί να είναι noble/jammy)
ROS_DISTRO="humble"
UBUNTU_CODENAME="$(. /etc/os-release && echo "$UBUNTU_CODENAME")"

echo "Installing ROS 2 $ROS_DISTRO for Ubuntu $UBUNTU_CODENAME..."

ROS_ALREADY_INSTALLED=0
if [ -d "/opt/ros/$ROS_DISTRO" ]; then
    ROS_ALREADY_INSTALLED=1
    echo "ROS 2 $ROS_DISTRO already present. Skipping ROS apt repo setup."
fi

# --- 1. Καθαρισμός & Locales ---
if [ "$ROS_ALREADY_INSTALLED" -eq 0 ]; then
    sudo rm -f /etc/apt/sources.list.d/*ros*.list
    sudo rm -f /etc/apt/sources.list.d/*ros*.sources
    sudo rm -f /usr/share/keyrings/ros-archive-keyring.gpg
fi

if ! has_apt_pkg locales; then
    sudo apt update
    sudo apt install -y locales
fi
if ! locale -a | grep -q "en_US.utf8"; then
    sudo locale-gen en_US en_US.UTF-8
fi
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# --- 2. Προσθήκη Αποθετηρίων & Κλειδιών ---
if ! has_apt_pkg software-properties-common || ! has_apt_pkg curl; then
    sudo apt update
    sudo apt install -y software-properties-common curl
fi
sudo add-apt-repository -y universe

if [ "$ROS_ALREADY_INSTALLED" -eq 0 ]; then
    sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $UBUNTU_CODENAME main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
fi

# --- 3. Εγκατάσταση ROS 2 ---
sudo apt update
sudo apt upgrade -y
if [ "$ROS_ALREADY_INSTALLED" -eq 0 ]; then
    sudo apt install -y ros-humble-desktop
fi
if ! has_apt_pkg python3-colcon-common-extensions || ! has_apt_pkg python3-rosdep || ! has_apt_pkg python3-argcomplete; then
    sudo apt install -y python3-colcon-common-extensions python3-rosdep python3-argcomplete
fi

# Setup περιβάλλοντος για το τρέχον session
source /opt/ros/humble/setup.bash
grep -q "source /opt/ros/humble/setup.bash" ~/.bashrc || echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc

# --- 4. Εγκατάσταση uv ---
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Ενημέρωση PATH για το τρέχον script
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# Βεβαιώσου ότι το uv είναι διαθέσιμο στο PATH
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

# --- 5. Aliases ---
grep -q "alias s=" ~/.bashrc || echo "alias s='source .venv_vision/bin/activate && source install/setup.bash'" >> ~/.bashrc
grep -q "alias b=" ~/.bashrc || echo "alias b='source .venv_vision/bin/activate && colcon build --symlink-install && source install/setup.bash'" >> ~/.bashrc

# --- 6. Virtual Environment (Vision) ---
if [ ! -d ".venv_vision" ] || [ ! -x ".venv_vision/bin/python" ]; then
    echo "Creating virtual environment..."
    rm -rf .venv_vision
    uv venv .venv_vision --python python3
fi

source .venv_vision/bin/activate

if ! python -m pip --version &> /dev/null; then
    uv pip install pip
fi

if [ -f "requirements_vision.txt" ]; then
    REQ_HASH_FILE=".venv_vision/.requirements_vision.hash"
    REQ_HASH=$(hash_file requirements_vision.txt)
    if [ "$FORCE" -eq 1 ] || [ ! -f "$REQ_HASH_FILE" ] || [ "$(cat "$REQ_HASH_FILE")" != "$REQ_HASH" ]; then
        echo "Installing requirements..."
        uv pip install -r requirements_vision.txt
        echo "$REQ_HASH" > "$REQ_HASH_FILE"
    else
        echo "Requirements already installed (hash match)."
    fi
fi

# --- 6b. PyTorch CUDA Compatibility ---
CUDA_VERSION=""
if command -v nvidia-smi &> /dev/null; then
    CUDA_VERSION=$(nvidia-smi | sed -n 's/.*CUDA Version: \([0-9.]*\).*/\1/p' | head -n 1)
fi

TORCH_CUDA_TAG=""
case "$CUDA_VERSION" in
    12.2*) TORCH_CUDA_TAG="cu121" ;;
    12.1*) TORCH_CUDA_TAG="cu121" ;;
    12.0*) TORCH_CUDA_TAG="cu120" ;;
    11.8*) TORCH_CUDA_TAG="cu118" ;;
esac

TORCH_VERSION_SPEC=""
TORCHVISION_VERSION_SPEC=""
if [ "$TORCH_CUDA_TAG" = "cu121" ]; then
    TORCH_VERSION_SPEC="torch==2.2.0+cu121"
    TORCHVISION_VERSION_SPEC="torchvision==0.17.0+cu121"
fi

NEEDS_TORCH_INSTALL=1
if [ "$FORCE" -eq 0 ] && python -c "import torch" &> /dev/null; then
    TORCH_VERSION=$(python - <<'PY'
import torch
print(torch.__version__)
print(torch.version.cuda or "")
PY
)
    TORCH_BUILD=$(echo "$TORCH_VERSION" | tail -n 1)
    if [ -n "$TORCH_CUDA_TAG" ] && [ -n "$TORCH_BUILD" ]; then
        case "$TORCH_CUDA_TAG" in
            cu122) [ "$TORCH_BUILD" = "12.2" ] && NEEDS_TORCH_INSTALL=0 ;;
            cu121) [ "$TORCH_BUILD" = "12.1" ] && NEEDS_TORCH_INSTALL=0 ;;
            cu120) [ "$TORCH_BUILD" = "12.0" ] && NEEDS_TORCH_INSTALL=0 ;;
            cu118) [ "$TORCH_BUILD" = "11.8" ] && NEEDS_TORCH_INSTALL=0 ;;
        esac
    elif [ -z "$TORCH_CUDA_TAG" ] && [ -z "$TORCH_BUILD" ]; then
        NEEDS_TORCH_INSTALL=0
    fi
fi

if [ "$FORCE" -eq 1 ]; then
    NEEDS_TORCH_INSTALL=1
fi

if [ "$NEEDS_TORCH_INSTALL" -eq 1 ]; then
    if [ -n "$TORCH_CUDA_TAG" ]; then
        echo "Installing PyTorch for CUDA $CUDA_VERSION ($TORCH_CUDA_TAG)..."
        if [ -n "$TORCH_VERSION_SPEC" ]; then
            uv pip install --upgrade --index-url "https://download.pytorch.org/whl/$TORCH_CUDA_TAG" \
                --extra-index-url "https://pypi.org/simple" --index-strategy unsafe-best-match \
                "$TORCH_VERSION_SPEC" "$TORCHVISION_VERSION_SPEC"
        else
            uv pip install --upgrade --index-url "https://download.pytorch.org/whl/$TORCH_CUDA_TAG" \
                --extra-index-url "https://pypi.org/simple" --index-strategy unsafe-best-match \
                torch torchvision
        fi
    else
        echo "CUDA version not detected; installing CPU-only PyTorch..."
        uv pip install --upgrade --index-url "https://download.pytorch.org/whl/cpu" \
            --extra-index-url "https://pypi.org/simple" --index-strategy unsafe-best-match \
            torch torchvision
    fi
else
    echo "PyTorch already compatible with detected CUDA version."
fi

# Re-apply numpy pin for cv_bridge compatibility
if [ -f "requirements_vision.txt" ]; then
    if grep -q "^numpy<2" requirements_vision.txt; then
        uv pip install "numpy<2"
    fi
fi

# --- 7. PYTHONPATH ---
export PYTHONPATH="$PYTHONPATH:$WS/external"
# Προαιρετικά: Πρόσθεσέ το και στο .bashrc αν θέλεις να μένει μόνιμα
# grep -q "PYTHONPATH" ~/.bashrc || echo "export PYTHONPATH=\"\$PYTHONPATH:$WS/external\"" >> ~/.bashrc

echo "Setup complete! Please run: source ~/.bashrc"
