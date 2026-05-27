camera feed inspection:

1. ros2 run opencv_cam opencv_cam_main
2. ros2 run rqt_image_view rqt_image_view

visualization of system

1. ros2 run rqt_graph rqt_graph

camera calibration: https://docs.nav2.org/tutorials/docs/camera_calibration.html

1. export PYTHONPATH=$(pwd)/.venv/lib/python3.10/site-packages:$PYTHONPATH
2. python3 /opt/ros/humble/lib/camera_calibration/cameracalibrator --no-service-check --size 7x9 --square 0.02 -p chessboard --ros-args -r image:=/image_raw

# inside the ORB container

ros2 run image_proc image_proc --ros-args \
 -r image:=/camera/color/image_raw \
 -r camera_info:=/camera/color/camera_info

and

change the `docker/ORB-SLAM3-ROS2-Docker/orb_slam3_ros2_wrapper/params/ros_params/gazebo-rgbd-imu-ros-params.yaml`

ros2 launch ros2 launch orb_slam3_ros2_wrapper rgbd_imu.launch.py

ros2 launch orb_slam3_ros2_wrapper mono.launch.py

ros2 launch orb_slam3_ros2_wrapper mono_imu.launch.py

you need to change the yaml

for micro ros client over wifi
docker run -it --rm -v /dev:/dev -v /dev/shm:/dev/shm --privileged --net=host microros/micro-ros-agent:$ROS_DISTRO udp4 --port 8888 -v6
