# image_to_depth_generation

ROS 2 package that runs Depth Anything V2 to produce depth images on demand and publish a point cloud.

## Nodes

### depth_anything_v2_node

Subscribes to an RGB image topic, caches the latest frame, and computes depth when the trigger service is called.

#### Topics

- Subscribes: `image_raw` (parameter: `input_topic`)
- Subscribes: `camera_info` (parameter: `camera_info_topic`)
- Publishes: `depth_image` (parameter: `output_topic`)
- Publishes: `pointcloud` (PointCloud2, parameter: `pointcloud_topic`)

#### Services

- `trigger_depth` (parameter: `service_name`)

#### Parameters

- `model_path` (string): Path to the checkpoint. Defaults to `assets/checkpoints/depth_anything_v2_vits.pth`.
- `input_topic` (string): RGB image topic name.
- `output_topic` (string): Depth image topic name.
- `service_name` (string): Trigger service name.
- `encoder` (string): Encoder name, e.g. `vits`.
- `features` (int): Feature size.
- `out_channels` (int array): Output channels per stage.
- `device` (string): `cpu`, `cuda`, or `auto`.
- `pointcloud_topic` (string): PointCloud2 topic name.
- `camera_info_topic` (string): CameraInfo topic name used for intrinsics.

#### Point cloud generation

The node converts each valid depth pixel to XYZ using a simple pinhole model:

$$
X = (u - c_x) \cdot z / f_x\quad
Y = (v - c_y) \cdot z / f_y\quad
Z = z
$$

Camera intrinsics are taken from the latest CameraInfo message.

## Build

```bash
cd /workspace
colcon build --symlink-install
source install/setup.bash
```

## Run

```bash
ros2 launch image_to_depth_generation depth_anything.launch.py
```

## Trigger

```bash
ros2 service call /trigger_depth std_srvs/srv/Trigger {}
```

## Visualize

Use RViz2 and add a PointCloud2 display for the topic `pointcloud` (or your remapped topic).
