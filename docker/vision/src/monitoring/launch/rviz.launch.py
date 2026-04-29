from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    rviz_config = LaunchConfiguration("rviz_config")

    use_config = PythonExpression(["'", rviz_config, "' != ''"])
    no_config = PythonExpression(["'", rviz_config, "' == ''"])

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "rviz_config",
                default_value="",
                description="Path to an RViz config file (optional).",
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                condition=IfCondition(use_config),
                arguments=["-d", rviz_config],
            ),
            Node(
                package="rviz2",
                executable="rviz2",
                name="rviz2",
                output="screen",
                condition=IfCondition(no_config),
            ),
        ]
    )
