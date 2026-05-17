#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from actuator_msgs.msg import Actuators
import sys, select, termios, tty

msg = """
Control Your Drone Rotors!
---------------------------
Rotor 0: Press 'q' to increase, 'a' to decrease
Rotor 1: Press 'w' to increase, 's' to decrease

Spacebar : STOP ALL ROTORS
CTRL-C to quit
"""

class DroneTeleop(Node):
    def __init__(self):
        super().__init__('drone_teleop')
        # Matches your exact YAML bridge topic and message type
        self.publisher_ = self.create_publisher(Actuators, '/drone/command/motor_speed', 10)
        self.timer = self.create_timer(0.02, self.timer_callback) # 50 Hz stream
        self.speeds = [0.0, 0.0] # [Rotor 0, Rotor 1]
        print(msg)

    def timer_callback(self):
        cmd = Actuators()
        cmd.velocity = self.speeds
        self.publisher_.publish(cmd)
        # Dynamic console printout to see current speeds
        sys.stdout.write(f"\rCurrent Motor Speeds -> Rotor 0: {self.speeds[0]:.1f} | Rotor 1: {self.speeds[1]:.1f}   ")
        sys.stdout.flush()

def getKey(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = DroneTeleop()

    try:
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=0.01)
            key = getKey(settings)
            if key == 'q':
                node.speeds[0] += 50.0
            elif key == 'a':
                node.speeds[0] = max(0.0, node.speeds[0] - 50.0)
            elif key == 'w':
                node.speeds[1] += 50.0
            elif key == 's':
                node.speeds[1] = max(0.0, node.speeds[1] - 50.0)
            elif key == ' ':
                node.speeds = [0.0, 0.0]
            elif key == '\x03': # Ctrl+C
                break
    except Exception as e:
        print(e)
    finally:
        node.speeds = [0.0, 0.0]
        node.timer_callback()
        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
