from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    joy_topic = LaunchConfiguration('joy_topic')
    publish_rate_hz = LaunchConfiguration('publish_rate_hz')
    control_mode_service = LaunchConfiguration('control_mode_service')
    position_target_service = LaunchConfiguration('position_target_service')
    target_step_xy_m = LaunchConfiguration('target_step_xy_m')
    target_step_z_m = LaunchConfiguration('target_step_z_m')
    target_step_yaw_deg = LaunchConfiguration('target_step_yaw_deg')

    return LaunchDescription([
        DeclareLaunchArgument(
            'joy_topic',
            default_value='/joy',
            description='Joy output topic for the GUI publisher',
        ),
        DeclareLaunchArgument(
            'publish_rate_hz',
            default_value='20.0',
            description='Joy publish rate in Hz',
        ),
        DeclareLaunchArgument(
            'control_mode_service',
            default_value='/drone/set_control_mode',
            description='Control mode service for the GUI',
        ),
        DeclareLaunchArgument(
            'position_target_service',
            default_value='/drone/set_position_target',
            description='Position target service for the GUI',
        ),
        DeclareLaunchArgument(
            'target_step_xy_m',
            default_value='0.10',
            description='Default XY target step in meters',
        ),
        DeclareLaunchArgument(
            'target_step_z_m',
            default_value='0.05',
            description='Default Z target step in meters',
        ),
        DeclareLaunchArgument(
            'target_step_yaw_deg',
            default_value='10.0',
            description='Default yaw target step in degrees',
        ),
        Node(
            package='drone_control',
            executable='joy_gui_publisher',
            name='joy_gui_publisher',
            output='screen',
            parameters=[{
                'joy_topic': joy_topic,
                'publish_rate_hz': publish_rate_hz,
                'control_mode_service': control_mode_service,
                'position_target_service': position_target_service,
                'target_step_xy_m': target_step_xy_m,
                'target_step_z_m': target_step_z_m,
                'target_step_yaw_deg': target_step_yaw_deg,
            }],
        ),
    ])