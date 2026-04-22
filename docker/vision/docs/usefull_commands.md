
camera feed inspection:
ros2 run rqt_image_view rqt_image_view

visualization of system
ros2 run rqt_graph rqt_graph

export TURTLEBOT3_MODEL=waffle
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp # if the other not working


ros2 launch turtlebot3_cartographer cartographer.launch.py use_sim_time:=True
ros2 run turtlebot3_teleop teleop_keyboard 
ros2 run nav2_map_server map_saver_cli -f assets/maps/my_map

ros2 launch turtlebot3_navigation2 navigation2.launch.py use_sim_time:=True map:=assets/maps/my_map.yaml

# custom world gazebo
gazebo my_world.world
