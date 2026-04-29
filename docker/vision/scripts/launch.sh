#!/bin/bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp

# Ενεργοποίηση των aliases μέσα στο script
shopt -s expand_aliases

# Αρχικό Setup Περιβάλλοντος
source /opt/ros/humble/setup.bash
[ -f ".venv/bin/activate" ] && source .venv/bin/activate
[ -f "install/setup.bash" ] && source install/setup.bash

WS="/workspace"
DEFAULT_DELAY=0.1
DEFAULT_LONG_DELAY=0.2
# Η εντολή που προετοιμάζει κάθε νέο terminal panel
GLOBAL_CMD="cd $WS && source /opt/ros/humble/setup.bash && source $WS/install/setup.bash && source $WS/.venv/bin/activate && export PYTHONPATH=\$PYTHONPATH:$WS/external"
LAYOUT_NAME="VisionTest"

# Aliases για πλοήγηση και λειτουργίες
alias move_up="xdotool key Alt+Up && sleep $DEFAULT_DELAY"
alias move_down="xdotool key Alt+Down && sleep $DEFAULT_DELAY"
alias move_left="xdotool key Alt+Left && sleep $DEFAULT_DELAY"
alias move_right="xdotool key Alt+Right && sleep $DEFAULT_DELAY"
alias broadcast_on="xdotool key Super+g && sleep $DEFAULT_LONG_DELAY && xdotool key shift+ctrl+a && sleep $DEFAULT_DELAY"
alias broadcast_off="xdotool key Super+g && sleep $DEFAULT_LONG_DELAY && xdotool key shift+ctrl+h && $DEFAULT_DELAY"
alias enter="xdotool key Return && sleep $DEFAULT_DELAY"

# Συνάρτηση για επικόλληση και εκτέλεση εντολής
paste_cmd() {
    local text="$1"
    echo -n "$text" | xclip -selection clipboard
    sleep $DEFAULT_DELAY
    xdotool key ctrl+shift+v
    sleep $DEFAULT_DELAY
}

# 1. Εκκίνηση του Terminator με το layout
echo "Launching terminator with layout: $LAYOUT_NAME"
terminator -u -g $WS/terminator_config -l $LAYOUT_NAME &

# Περίμενε να φορτώσει το γραφικό περιβάλλον
sleep 0.5

# 2. Εστίαση στο παράθυρο του Terminator
MAX_RETRIES=10
WID=""
while [ -z "$WID" ] && [ $MAX_RETRIES -gt 0 ]; do
    WID=$(xdotool search --onlyvisible --class "terminator" | tail -1)
    [ -z "$WID" ] && sleep 1
    ((MAX_RETRIES--))
done

if [ -z "$WID" ]; then
    echo "Error: Terminator window not found."
    exit 1
fi

xdotool windowactivate $WID
sleep $DEFAULT_LONG_DELAY

# 3. Προετοιμασία: Σιγουρεύουμε ότι είμαστε στο πάνω panel
move_up
move_left

# configuration broadcasting
echo "Enabling broadcasting for all panels..."
broadcast_on
paste_cmd "$GLOBAL_CMD && clear" 
enter
broadcast_off

# --- PANEL 1 (Πάνω): Camera Input Node ---
echo "Configuring Panel 1..."
paste_cmd 'ros2 run gscam gscam_node --ros-args \
  -p gscam_config:="v4l2src device=/dev/video2 ! video/x-raw,width=720,height=480 ! videoconvert" \
  -p camera_info_url:=file:///workspace/assets/calibrations/webcam/ost.yaml \
  -p camera_name:=webcam \
  --remap /camera/image_raw:=/webcam/image_raw \
  --remap /camera/camera_info:=/webcam/camera_info
'
enter

# --- PANEL 2 (Κάτω): Depth Estimation Node ---
echo "Configuring Panel 2..."
move_down
paste_cmd "ros2 run rqt_image_view rqt_image_view"

# --- PANEL 3 (Δεξιά): Depth Image View ---
echo "Configuring Panel 3..."
move_up
move_right
paste_cmd "ros2 launch image_to_depth_generation depth_anything.launch.py"
enter

# -- Monitoring (RViz) ---
move_down
move_down
paste_cmd "ros2 launch monitoring rviz.launch.py rviz_config:=assets/rviz/monitoring.rviz"

# paste_cmd "ros2 run image_to_depth_generation depth_anything_v2_node --ros-args \
#   -p model_path:=/workspace/assets/checkpoints/depth_anything_v2_vits.pth \
#   -p input_topic:=/webcam/image_raw \
#   -p output_topic:=/webcam/depth_image \
#   -p service_name:=/webcam/trigger_depth
# "







# for drone camera pannel
# ros2 run gscam gscam_node --ros-args   -p gscam_config:="v4l2src device=/dev/video0 ! video/x-raw,width=720,height=480 ! videoconvert"   -p camera_info_url:=file:///workspace/assets/calibrations/drone/ost.yaml   -p camera_name:=drone   --remap /camera/image_raw:=/drone/image_raw   --remap /camera/camera_info:=/drone/camera_info
# ros2 run rqt_image_view rqt_image_view
# ros2 run image_to_depth_generation depth_anything_v2_node --ros-args   -p model_path:=/workspace/assets/checkpoints/depth_anything_v2_vits.pth   -p input_topic:=/drone/image_raw   -p output_topic:=/drone/depth_image   -p service_name:=/drone/trigger_depth





















echo "Setup complete."
