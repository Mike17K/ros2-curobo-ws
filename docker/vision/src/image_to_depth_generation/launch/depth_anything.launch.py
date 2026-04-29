from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    namespace = LaunchConfiguration("namespace")

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "namespace",
                default_value="webcam",
                description="Namespace for input/output topics.",
            ),
            Node(
                package="image_to_depth_generation",
                executable="depth_anything_v2_node",
                name="depth_anything_v2_node",
                namespace=namespace,
                output="screen",
                parameters=[
                    {
                        "model_path": "/workspace/assets/checkpoints/depth_anything_v2_vits.pth",

                        # IMPORTANT: match model
                        "encoder": "vits",
                        "features": 64,
                        "out_channels": [48, 96, 192, 384],

                        # device: auto / cuda / cpu
                        "device": "auto",
                    }
                ],
            )
        ]
    )