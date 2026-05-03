import rclpy
from rclpy.node import Node

from sensor_msgs.msg import Image, Imu


class TimeSyncNode(Node):
    def __init__(self):
        super().__init__('time_sync_node')

        # Declare parameters (fully configurable)
        self.declare_parameter('image_topic', '/image')
        self.declare_parameter('imu_topic', '/imu')
        self.declare_parameter('image_out_topic', '/image_sync')
        self.declare_parameter('imu_out_topic', '/imu_sync')
        self.declare_parameter('override_frame_id', '')

        # Get parameters
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        imu_topic = self.get_parameter('imu_topic').get_parameter_value().string_value
        image_out = self.get_parameter('image_out_topic').get_parameter_value().string_value
        imu_out = self.get_parameter('imu_out_topic').get_parameter_value().string_value
        self.override_frame_id = self.get_parameter('override_frame_id').get_parameter_value().string_value

        # Subscribers
        self.image_sub = self.create_subscription(
            Image, image_topic, self.image_callback, 10)

        self.imu_sub = self.create_subscription(
            Imu, imu_topic, self.imu_callback, 100)

        # Publishers
        self.image_pub = self.create_publisher(Image, image_out, 10)
        self.imu_pub = self.create_publisher(Imu, imu_out, 100)

        self.latest_image_stamp = None

        self.get_logger().info(f"Subscribed to: {image_topic}, {imu_topic}")
        self.get_logger().info(f"Publishing to: {image_out}, {imu_out}")

    def image_callback(self, msg: Image):
        self.latest_image_stamp = msg.header.stamp

        if self.override_frame_id:
            msg.header.frame_id = self.override_frame_id

        self.image_pub.publish(msg)

    def imu_callback(self, msg: Imu):
        if self.latest_image_stamp is not None:
            msg.header.stamp = self.latest_image_stamp

        if self.override_frame_id:
            msg.header.frame_id = self.override_frame_id

        self.imu_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TimeSyncNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()