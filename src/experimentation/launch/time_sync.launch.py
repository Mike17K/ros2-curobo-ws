from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        Node(
            package='experimentation',
            executable='time_sync_node',
            name='time_sync',
            namespace='sync',   # 👈 change or remove as needed

            parameters=[{
                'image_topic': '/webcam/image_raw',
                'image_out_topic': '/webcam/image_sync',
                'imu_topic': '/imu/data_raw',
                'imu_out_topic': '/imu/data_sync',
                'override_frame_id': 'imu_link'  # optional
            }],

            output='screen'
        )

    ])