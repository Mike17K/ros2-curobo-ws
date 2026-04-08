# --- Config ---
SHELL      := /bin/bash
ROS_DISTRO := humble
WS_ROOT    := $(shell pwd)
# Χρησιμοποιούμε το uv run για να εκτελούμε εντολές εντός του venv αυτόματα
RUN        := cd $(WS_ROOT) && source /opt/ros/$(ROS_DISTRO)/setup.bash && source .venv/bin/activate && uv run
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/opt/hpcx/ucx/lib:/opt/hpcx/ucc/lib

# Colors
G=\033[0;32m
Y=\033[0;33m
R=\033[0;31m
C=\033[0;36m
RESET=\033[0m

.PHONY: all build debug builds pkg clean deps create-cpp create-py dev sync

CMAKE_DEFAULT_FLAGS = -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# 1. Build & Sync (Το sync ενημερώνει το venv βάσει του pyproject.toml)
all: sync build

activate:
	@echo -e "$(C)Activating virtual environment...$(RESET)"
	source .venv/bin/activate

sync:
	@echo -e "$(C)Syncing dependencies with uv...$(RESET)"
	UV_CONCURRENT_BUILDS=1 MAX_JOBS=2 nice -n 15 uv sync

build:
	@echo -e "$(G)Building all packages...$(RESET)"
	export LD_LIBRARY_PATH=$${LD_LIBRARY_PATH}:/opt/hpcx/ucx/lib:/opt/hpcx/ucc/lib && \
	$(RUN) colcon build --symlink-install \
	--parallel-workers 2 \
	--base-paths src \
	--cmake-args $(CMAKE_DEFAULT_FLAGS) -DCMAKE_BUILD_TYPE=Release

# 2. Build Single Package (make builds n=όνομα)
builds:
	@if [ -z "$(n)" ]; then echo -e "$(R)Error: Provide name (n=name)$(RESET)"; exit 1; fi
	$(RUN) colcon build --packages-select $(n) --symlink-install --base-paths src --cmake-args $(CMAKE_DEFAULT_FLAGS) -DCMAKE_BUILD_TYPE=Release

# 3. Δημιουργία Πακέτων
create-cpp:
	@if [ -z "$(n)" ]; then echo -e "$(R)Error: Provide name (n=name)$(RESET)"; exit 1; fi
	cd src && ros2 pkg create --build-type ament_cmake $(n)

create-py:
	@if [ -z "$(n)" ]; then echo -e "$(R)Error: Provide name (n=name)$(RESET)"; exit 1; fi
	cd src && ros2 pkg create --build-type ament_python $(n)

# 4. Debug & Deps
debug:
	$(RUN) colcon build --symlink-install --base-paths src --cmake-args $(CMAKE_DEFAULT_FLAGS) -DCMAKE_BUILD_TYPE=Debug

debugs:
	$(RUN) colcon build --packages-select $(n) --symlink-install --base-paths src --cmake-args $(CMAKE_DEFAULT_FLAGS) -DCMAKE_BUILD_TYPE=Debug

deps:
	$(RUN) rosdep install -i --from-path src --rosdistro $(ROS_DISTRO) -y

# 5. Maintenance
clean:
	@echo -e "$(Y)Cleaning workspace...$(RESET)"
	rm -rf build/ install/ log/ .venv/


# 6. UV Package Management
# Χρήση: make add n=package_name
add:
	@if [ -z "$(n)" ]; then echo -e "$(R)Error: Provide package name (n=package)$(RESET)"; exit 1; fi
	@echo -e "$(C)Adding package $(n) with uv...$(RESET)"
	uv add $(n)

# Χρήση: make add-dev n=package_name (για εργαλεία όπως black, pytest)
add-dev:
	@if [ -z "$(n)" ]; then echo -e "$(R)Error: Provide package name (n=package)$(RESET)"; exit 1; fi
	uv add --dev $(n)

# Χρήση: make run n=package_name e=executable_name
run: builds
	@if [ -z "$(e)" ]; then echo -e "$(R)Error: Provide executable name (e=exec)$(RESET)"; exit 1; fi
	@echo -e "$(G)Running $(n)/$(e)...$(RESET)"
	source install/setup.bash && ros2 run $(n) $(e)

dev:
	@chmod +x scripts/*.sh
	./scripts/run_layout.sh
