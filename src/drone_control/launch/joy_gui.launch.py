from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    joy_topic = LaunchConfiguration('joy_topic')
    publish_rate_hz = LaunchConfiguration('publish_rate_hz')

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
        Node(
            package='drone_control',
            executable='joy_gui_publisher',
            name='joy_gui_publisher',
            output='screen',
            parameters=[{
                'joy_topic': joy_topic,
                'publish_rate_hz': publish_rate_hz,
            }],
        ),
    ])