source /opt/ros/humble/setup.bash
source .venv_vision/bin/activate

# Ensure colcon uses the venv Python (avoid system python during package discovery)
export COLCON_PYTHON_EXECUTABLE="$(pwd)/.venv_vision/bin/python"
export PYTHON_EXECUTABLE="$(pwd)/.venv_vision/bin/python"

# Ensure uv is on PATH in non-interactive shells
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
export PYTHONPATH=/workspace/external:$PYTHONPATH

# Ensure colcon is available in the venv so it uses the venv interpreter
if ! python -m colcon --help > /dev/null 2>&1; then
	uv pip install colcon-common-extensions
fi

python -m colcon build \
	--symlink-install \
	--parallel-workers 2 \
	--packages-select image_to_depth_generation \
	--cmake-args -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release