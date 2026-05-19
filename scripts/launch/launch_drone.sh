#!/bin/bash

ROS_DOMAIN_ID=55
ROS_DISTRO="jazzy"
WS="/home/kaipis/Desktop/projects/robotics/ros2-curobo-ws"
DEFAULT_DELAY=0.2
DEFAULT_LONG_DELAY=0.4
# Η εντολή που προετοιμάζει κάθε νέο terminal panel
GLOBAL_CMD="cd $WS && source /opt/ros/$ROS_DISTRO/setup.bash && source $WS/install/setup.bash && source $WS/.venv/bin/activate && export PYTHONPATH=\$PYTHONPATH:$WS/external && export ROS_DOMAIN_ID=$ROS_DOMAIN_ID"
LAYOUT_NAME="VisionTest"
TERMINATOR_CONFIG="$WS/scripts/config/drone.terminator_config"

source $WS/scripts/utils.sh

open_terminator


# # 3. Προετοιμασία: Σιγουρεύουμε ότι είμαστε στο πάνω panel
move_up
move_left

# configuration broadcasting
echo "Enabling broadcasting for all panels..."
broadcast_on
paste_cmd "$GLOBAL_CMD && clear" 
enter
broadcast_off

# --- PANEL 1 (Πάνω): Camera Input Node ---
echo "Configuring Panel 1..."
# export ogre_flags="--use-software-renderer"
# export GZ_RENDERING_BACKEND=ogre2
# export LIBGL_ALWAYS_SOFTWARE=1
# ros2 launch simulation gazebo.launch.py
paste_cmd 'ros2 launch simulation gazebo.launch.py'
# enter


move_right
split_vertical
paste_cmd 'ros2 launch drone_control joy_gui.launch.py'
move_left
paste_cmd "ros2 run tf2_ros static_transform_publisher 1.0 0.0 2.0 0.0 0.0 0.0 1.0 map base_footprint"
move_right
# enter

move_down
paste_cmd "ros2 run rviz2 rviz2 --ros-args -p description_topic:=/drone/robot_description"

move_left
paste_cmd 'ros2 launch drone_control drone_controller.launch.py'
# enter


# # --- PANEL 3 (Δεξιά): Depth Image View ---
# echo "Configuring Panel 3..."
# move_up
# move_right
# paste_cmd "ros2 launch image_to_depth_generation depth_anything.launch.py"
# enter

# # -- Monitoring (RViz) ---
# move_down
# move_down
# paste_cmd "ros2 launch monitoring rviz.launch.py rviz_config:=assets/rviz/monitoring.rviz"

# paste_cmd "ros2 run image_to_depth_generation depth_anything_v2_node --ros-args \
#   -p model_path:=/workspace/assets/checkpoints/depth_anything_v2_vits.pth \
#   -p input_topic:=/webcam/image_raw \
#   -p output_topic:=/webcam/depth_image \
#   -p service_name:=/webcam/trigger_depth
# "







# for drone camera pannel
# ros2 run gscam gscam_node --ros-args   -p gscam_config:="v4l2src device=/dev/video0 ! video/x-raw,width=720,height=480 ! videoconvert"   -p camera_info_url:=file:///workspace/assets/calibrations/drone/ost.yaml   -p camera_name:=drone   --remap /camera/image_raw:=/drone/image_raw   --remap /camera/camera_info:=/drone/camera_info
# ros2 run rqt_image_view rqt_image_view
# ros2 run image_to_depth_generation depth_anything_v2_node --ros-args   -p model_path:=/workspace/assets/checkpoints/depth_anything_v2_vits.pth   -p input_topic:=/drone/image_raw   -p output_topic:=/drone/depth_image   -p service_name:=/drone/trigger_depth

