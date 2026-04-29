import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():

    # =========================
    # 1. Gazebo Classic world
    # =========================
    world_path = PathJoinSubstitution([
        FindPackageShare('simulation'),
        'worlds',
        'drone_world.world'   # Gazebo Classic uses .world (NOT .sdf)
    ])

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('gazebo_ros'),
                'launch',
                'gazebo.launch.py'
            ])
        ]),
        launch_arguments={'world': world_path}.items(),
    )

    # =========================
    # 2. Spawn robot (Classic)
    # =========================
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'my_robot',
            '-topic', 'robot_description',
            '-z', '0.5'
        ],
        output='screen',
    )

    # =========================
    # 3. ROS-Gazebo bridge (Classic plugins only)
    # =========================
    # NOTE: Gazebo Classic uses gazebo_ros plugins inside URDF
    # NOT ros_gz_bridge

    # =========================
    # 4. Camera bridge (Classic)
    # =========================
    # In Gazebo Classic camera topics are already ROS topics via plugins

    return LaunchDescription([
        gazebo,
        spawn_robot,
    ])