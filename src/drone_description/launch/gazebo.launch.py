import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    pkg_description = get_package_share_directory('drone_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='empty.sdf',
        description='Gazebo world file to load',
    )

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': [TextSubstitution(text='-r '), LaunchConfiguration('world')]
        }.items(),
    )

    nodes = [world_arg, gazebo]

    try:
        get_package_share_directory('ros_gz_bridge')
        bridge_params = os.path.join(pkg_description, 'config', 'gz_bridge.yaml')
        ros_gz_bridge = Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            output='screen',
            parameters=[{'use_sim_time': True}],
            arguments=['--ros-args', '-p', f'config_file:={bridge_params}'],
        )
        nodes.append(ros_gz_bridge)
    except PackageNotFoundError:
        pass

    return LaunchDescription(nodes)