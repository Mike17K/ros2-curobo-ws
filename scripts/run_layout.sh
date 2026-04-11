#!/bin/bash

paste_cmd() {
    local text="$1"
    echo -n "$text" | xclip -selection clipboard
    sleep 0.1
    xdotool key ctrl+shift+v
}

move_up() {
    xdotool key Alt+Up
}
move_down() {
    xdotool key Alt+Down
}
move_left() {
    xdotool key Alt+Left
}
move_right() {
    xdotool key Alt+Right
}

broadcast_cmd() {
    local cmd="$1"
    xdotool key Super+g
    sleep 0.5
    xdotool key shift+ctrl+a
    paste_cmd "$cmd"
    xdotool key Return
    xdotool key shift+ctrl+h
}


WS="/home/kaipis/Desktop/projects/robotics/curobo-test"
GLOBAL_CMD="cd $WS && source /opt/ros/jazzy/setup.bash && source $WS/install/setup.bash && source $WS/.venv/bin/activate"
LAYOUT_NAME="CuroboTest"

# Launch Terminator with your saved layout
terminator -l $LAYOUT_NAME &
sleep 1

# Get the newest Terminator window
WID=$(xdotool search --class "terminator" | tail -1)
xdotool windowactivate $WID
sleep 0.5
    
# Run GLOBAL_CMD in all panes
broadcast_cmd "$GLOBAL_CMD"
sleep 0.5

# Make sure we're back to first pane
move_up
move_up
move_up
move_up
move_up
move_up
move_up
move_left
move_left
move_left
move_left
move_left
move_left
move_left
sleep 0.5

# Run ROS2 only in main pane
paste_cmd "ros2 run opencv_cam opencv_cam_main" && xdotool key Return
move_right
paste_cmd "ros2 run rqt_image_view rqt_image_view" && xdotool key Return
