from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    imu_topic = LaunchConfiguration('imu_topic')
    joy_topic = LaunchConfiguration('joy_topic')
    motor_topic = LaunchConfiguration('motor_topic')
    namespace = LaunchConfiguration('namespace')

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace',
            default_value='drone',
            description='Robot namespace for the controller node',
        ),
        DeclareLaunchArgument(
            'imu_topic',
            default_value='/drone/imu',
            description='Input IMU topic',
        ),
        DeclareLaunchArgument(
            'joy_topic',
            default_value='/joy',
            description='Input joystick topic, typically sensor_msgs/msg/Joy',
        ),
        DeclareLaunchArgument(
            'motor_topic',
            default_value='/drone/command/motor_speed',
            description='Output motor command topic',
        ),
        Node(
            package='drone_control',
            executable='drone_controller',
            name='drone_controller',
            namespace=namespace,
            output='screen',
            remappings=[
                ('imu', imu_topic),
                ('joy', joy_topic),
                ('motor_speed', motor_topic),
            ],
        ),
    ])