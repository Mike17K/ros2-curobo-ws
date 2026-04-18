source /opt/ros/humble/setup.bash
source .venv/bin/activate
source install/setup.bash

# ros2 run image_to_depth_generation depth_analyzer_node
ros2 run image_to_depth_generation depth_anything_v2_node 