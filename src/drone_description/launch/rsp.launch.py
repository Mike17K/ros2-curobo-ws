import os
import xacro
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # 1. Process the Xacro file
    pkg_path = os.path.join(get_package_share_directory("drone_description"))
    xacro_file = os.path.join(pkg_path, "description", "drone.urdf.xacro")
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # 2. Setup the Robot State Publisher node
    node_robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description_raw, "use_sim_time": True}],
    )

    return LaunchDescription([node_robot_state_publisher])
