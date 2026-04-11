
camera feed inspection:
1. ros2 run opencv_cam opencv_cam_main
2. ros2 run rqt_image_view rqt_image_view

camera calibration: https://docs.nav2.org/tutorials/docs/camera_calibration.html
1. export PYTHONPATH=$(pwd)/.venv/lib/python3.10/site-packages:$PYTHONPATH
2. python3 /opt/ros/humble/lib/camera_calibration/cameracalibrator --no-service-check --size 7x9 --square 0.02 -p chessboard --ros-args -r image:=/image_raw
