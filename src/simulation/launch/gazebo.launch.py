import os

from ament_index_python.packages import get_package_share_directory, PackageNotFoundError
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, TextSubstitution
from launch_ros.actions import Node


def generate_launch_description():
    simulation_pkg_description = get_package_share_directory('simulation')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value=PathJoinSubstitution([simulation_pkg_description, 'worlds', 'drone_world.sdf']),
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

    # inclulde spawn_drone.launch.py to spawn the drone into the Gazebo world
    spawn_drone = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(simulation_pkg_description, 'launch', 'spawn_drone.launch.py')
        )
    )

    get_package_share_directory('ros_gz_bridge')
    bridge_params = os.path.join(simulation_pkg_description, 'config', 'gz_bridge.yaml')
    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['--ros-args', '-p', f'config_file:={bridge_params}'],
    )

    nodes = [world_arg, gazebo, spawn_drone, ros_gz_bridge]
    return LaunchDescription(nodes)