from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    depth_image_topic = LaunchConfiguration('depth_image_topic')
    camera_info_topic = LaunchConfiguration('camera_info_topic')
    pointcloud_topic = LaunchConfiguration('pointcloud_topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'depth_image_topic',
            default_value='/drone/camera/depth/image_raw',
            description='Depth image topic to convert into PointCloud2',
        ),
        DeclareLaunchArgument(
            'camera_info_topic',
            default_value='/drone/camera/depth/camera_info',
            description='Camera info topic for the depth camera',
        ),
        DeclareLaunchArgument(
            'pointcloud_topic',
            default_value='/drone/camera/depth/points',
            description='Output PointCloud2 topic',
        ),
        Node(
            package='depth_image_proc',
            executable='point_cloud_xyz_node',
            name='depth_to_pointcloud',
            output='screen',
            remappings=[
                ('image_rect', depth_image_topic),
                ('camera_info', camera_info_topic),
                ('points', pointcloud_topic),
            ],
        ),
    ])
