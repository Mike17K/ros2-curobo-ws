import os

from ament_index_python import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import PathJoinSubstitution, TextSubstitution
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    # 1. Path to Gazebo World
    world_path = PathJoinSubstitution([
        FindPackageShare('simulation'), 'worlds', 'drone_world.sdf'
    ])

    # 2. Include the Gazebo Server/Client launch
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py'
            ])
        ]),
        # Χρησιμοποιούμε λίστα για να ενώσουμε το string '-r ' με το substitution αντικείμενο
        launch_arguments={'gz_args': [TextSubstitution(text='-r '),world_path]}.items(),
    )

    # 3. Spawn the entity (The Robot)
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'my_robot',
            '-topic', 'robot_description', # Uses the robot_description topic from robot_state_publisher
            '-z', '0.5'
        ],
        output='screen',
    )

    bridge_params = os.path.join(get_package_share_directory('simulation'), 'config', 'gz_bridge.yaml')
    gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '--ros-args',
            '-p',
            f'config_file:={bridge_params}',
        ],            
    )

    ros_gz_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=["/camera/image_raw"]
    )

    return LaunchDescription([
        gz_sim, 
        spawn_robot,
        gz_bridge,
        ros_gz_image_bridge,
])