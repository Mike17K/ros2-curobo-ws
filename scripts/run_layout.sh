#!/bin/bash
WS="/home/kaipis/Desktop/projects/robotics/curobo-test"

# Σωστή σειρά: 1. ROS2 -> 2. Workspace -> 3. uv venv (τελευταίο για προτεραιότητα στην Python)
GLOBAL_CMD="source /opt/ros/jazzy/setup.bash && source $WS/install/setup.bash && source $WS/.venv/bin/activate"

# Στη Bash η συνένωση γίνεται απλά βάζοντας τις μεταβλητές τη μία δίπλα στην άλλη
CMD1="$GLOBAL_CMD && cd $WS && make"
CMD2="$GLOBAL_CMD && ros2 topic list"

# 1. Άνοιξε το πρώτο παράθυρο με την CMD1
# Χρησιμοποιούμε -u για να αποφύγουμε conflicts με dbus αν το terminator είναι ήδη ανοιχτό
terminator -u -e "$CMD1; exec bash" &

# Περίμενε να ανοίξει το παράθυρο (το Ubuntu 24 ίσως θέλει λίγο παραπάνω χρόνο)
sleep 2 

# 2. Εντοπισμός παραθύρου και Split
WID=$(xdotool search --class "terminator" | tail -1)
xdotool windowactivate $WID
xdotool key ctrl+shift+o

# 3. Στείλε την CMD2 στο νέο split
sleep 1
xdotool type "$CMD2"
xdotool key Return
