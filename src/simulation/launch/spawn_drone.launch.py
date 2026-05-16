import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    # 1. Locate package directories
    pkg_description = get_package_share_directory('drone_description')

    # 2. Declare launch arguments for flexibility
    ns_arg = DeclareLaunchArgument('namespace', default_value='drone', description='Robot namespace')
    x_pose = LaunchConfiguration('x', default='0.0')
    y_pose = LaunchConfiguration('y', default='0.0')
    z_pose = LaunchConfiguration('z', default='0.5') # Spawn slightly above the ground

    # 3. Parse Xacro to generate the URDF string dynamically
    xacro_file = os.path.join(pkg_description, 'description', 'drone.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_desc = {'robot_description': robot_description_config.toxml()}

    # 4. Node: Robot State Publisher (Processes URDF and streams TFs)
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        namespace=LaunchConfiguration('namespace'),
        parameters=[robot_desc, {'use_sim_time': True}]
    )

    # 5. Node: Spawn the drone entity into an already running Gazebo Sim
    spawn_drone = Node(
        package='ros_gz_sim',
        executable='create',
        output='screen',
        arguments=[
            '-string', robot_description_config.toxml(),
            '-name', LaunchConfiguration('namespace'),
            '-allow_renaming', 'true',
            '-x', x_pose,
            '-y', y_pose,
            '-z', z_pose
        ]
    )

    return LaunchDescription([
        ns_arg,
        robot_state_publisher,
        spawn_drone,
    ])
