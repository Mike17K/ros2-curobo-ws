import os
import sys
import threading
import time

import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import Image
from std_srvs.srv import Trigger
from cv_bridge import CvBridge
import torch

from ament_index_python.packages import get_package_share_directory


class DepthAnythingV2Node(Node):
    def __init__(self) -> None:
        super().__init__("depth_anything_v2_node")

        self.declare_parameter("model_path", "assets/checkpoints/depth_anything_v2_vits.pth")
        self.declare_parameter("input_topic", "image_raw")
        self.declare_parameter("output_topic", "depth_image")
        self.declare_parameter("service_name", "trigger_depth")
        self.declare_parameter("encoder", "vits")
        self.declare_parameter("features", 64)
        self.declare_parameter("out_channels", [48, 96, 192, 384])
        self.declare_parameter("device", "auto")

        model_path = self.get_parameter("model_path").get_parameter_value().string_value
        input_topic = self.get_parameter("input_topic").get_parameter_value().string_value
        output_topic = self.get_parameter("output_topic").get_parameter_value().string_value
        service_name = self.get_parameter("service_name").get_parameter_value().string_value
        encoder = self.get_parameter("encoder").get_parameter_value().string_value
        features = self.get_parameter("features").get_parameter_value().integer_value
        out_channels = self.get_parameter("out_channels").value
        device_param = self.get_parameter("device").get_parameter_value().string_value

        self.device = self._select_device(device_param)
        self.get_logger().info(f"Using device: {self.device}")

        self._model_path = self._resolve_model_path(model_path)
        self.model = None
        self._load_model(
            encoder=encoder,
            features=features,
            out_channels=list(out_channels),
        )

        self.bridge = CvBridge()
        self._lock = threading.Lock()
        self._last_image = None
        self._last_header = None

        self.image_sub = self.create_subscription(Image, input_topic, self._on_image, 10)
        self.depth_pub = self.create_publisher(Image, output_topic, 10)
        self.trigger_srv = self.create_service(Trigger, service_name, self._on_trigger)

        self.get_logger().info(
            f"Listening on '{input_topic}', publishing depth to '{output_topic}', service '{service_name}'"
        )

    def _select_device(self, device_param: str) -> str:
        if device_param == "cuda":
            if not torch.cuda.is_available():
                self.get_logger().warn("CUDA requested but not available, using CPU")
                return "cpu"
            return "cuda"
        if device_param == "cpu":
            return "cpu"
        return "cuda" if torch.cuda.is_available() else "cpu"

    def _resolve_model_path(self, model_path: str) -> str:
        if os.path.isabs(model_path):
            return model_path

        workspace_root = os.environ.get("WORKSPACE_ROOT", "/workspace")
        external_path = os.path.join(workspace_root, "external")
        if external_path not in sys.path:
            sys.path.insert(0, external_path)

        workspace_candidate = os.path.join(workspace_root, model_path)
        if os.path.isfile(workspace_candidate):
            return workspace_candidate

        try:
            share_dir = get_package_share_directory("image_to_depth_generation")
            share_candidate = os.path.join(share_dir, model_path)
            if os.path.isfile(share_candidate):
                return share_candidate
        except Exception:
            pass

        return model_path

    def _load_model(self, encoder: str, features: int, out_channels: list) -> None:
        if not os.path.isfile(self._model_path):
            self.get_logger().error(
                "Model file not found: %s. Set 'model_path' parameter to a valid checkpoint.",
                self._model_path,
            )
            return

        try:
            from depth_anything_v2.dpt import DepthAnythingV2
        except Exception as exc:
            self.get_logger().error("Failed to import depth_anything_v2: %s", exc)
            return

        self.model = DepthAnythingV2(
            encoder=encoder,
            features=features,
            out_channels=out_channels,
        )
        self.model.load_state_dict(torch.load(self._model_path, map_location="cpu"))
        self.model.to(self.device).eval()

    def _on_image(self, msg: Image) -> None:
        try:
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as exc:
            self.get_logger().error(f"Failed to convert image: {exc}")
            return

        with self._lock:
            self._last_image = image
            self._last_header = msg.header

    def _on_trigger(self, _request: Trigger.Request, response: Trigger.Response) -> Trigger.Response:
        if self.model is None:
            response.success = False
            response.message = "Model not loaded. Check 'model_path'."
            return response
        with self._lock:
            if self._last_image is None:
                response.success = False
                response.message = "No image received yet"
                return response
            image = self._last_image.copy()
            header = self._last_header

        start_time = time.time()
        with torch.no_grad():
            depth = self.model.infer_image(image)

        depth = np.asarray(depth, dtype=np.float32)
        depth_msg = self.bridge.cv2_to_imgmsg(depth, encoding="32FC1")
        if header is not None:
            depth_msg.header = header
        self.depth_pub.publish(depth_msg)

        response.success = True
        response.message = f"Depth published in {time.time() - start_time:.3f}s"
        return response


def main() -> None:
    rclpy.init()
    node = DepthAnythingV2Node()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
