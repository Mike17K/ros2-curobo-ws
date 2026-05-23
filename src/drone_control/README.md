# drone_control

This package turns joystick and IMU data into motor speed commands for a quadrotor.

It is written for ROS 2 and uses a two-layer controller:

- Outer layer: geometric attitude control on SO(3)
- Inner layer: angular-rate PID control

If those terms are new to you, this README explains them from first principles.

## 1) What this package does

At every control tick (default 50 Hz), the controller:

1. Reads latest joystick input (`sensor_msgs/msg/Joy`)
2. Reads latest orientation + gyro rates from IMU (`sensor_msgs/msg/Imu`)
3. Computes desired body moments (roll, pitch, yaw torque-like commands)
4. Mixes those moments into 4 motor speeds
5. Publishes motor speeds (`actuator_msgs/msg/Actuators`)

If joystick times out or deadman is not pressed, it publishes zero/min motor command.

## 2) ROS 2 basics you need

ROS 2 components used here:

- Node: a running process. Here the main node is `drone_controller`.
- Topic: named data stream. Nodes publish or subscribe.
- Message type: schema for topic data.
- Parameter: runtime config value (gain, topic name, limits, etc).
- Launch file: script that starts node(s) with arguments and parameters.

Main topics:

- IMU input: `/drone/imu` (default)
- Joystick input: `/joy` (default)
- Motor command output: `/drone/command/motor_speed` (default)

## 3) Why two control loops

A quadrotor is hard to stabilize because orientation dynamics are fast.
A common and practical structure is:

- Outer loop (slower conceptually): converts orientation error to desired angular rates
- Inner loop (fast): tracks angular rates using PID

This split is more robust than trying to do everything in one simple controller.

## 4) SO(3) in simple words

### 4.1 What SO(3) means

SO(3) is the set of all 3D rotations.

A rotation matrix R is in SO(3) if:

- R^T R = I (orthonormal)
- det(R) = 1

Why use this here:

- It avoids Euler-angle singularities (gimbal lock)
- It gives a clean, global way to compute orientation error
- It is standard in modern quadrotor control

### 4.2 How orientation error is computed

Current orientation from IMU quaternion is converted to rotation matrix R.
Desired rotation matrix is built from joystick commands:

- roll command -> Rx(phi)
- pitch command -> Ry(theta)
- yaw command -> Rz(psi)

Desired matrix:

Rd = Rz(psi*d) * Ry(theta*d) * Rx(phi_d)

Error matrix (skew-symmetric part):

E = 0.5 _ (Rd^T _ R - R^T \* Rd)

e_R (vector form) is obtained using the vee map from E.

Then desired body rates are generated:

- omega_des_x = K_R_attitude \* e_R_x
- omega_des_y = K_R_attitude \* e_R_y
- omega_des_z = K_R_yaw \* yaw_error

### 4.3 What the gains mean

- `K_R_attitude`: how strongly roll/pitch angle error becomes desired roll/pitch rate
- `K_R_yaw`: how strongly yaw angle error becomes desired yaw rate

Bigger gain -> faster correction but more oscillation risk.

When yaw is configured as a rate command, the roll/pitch reference is anchored to the current yaw frame so the aircraft does not lose roll/pitch authority after large yaw turns.

## 5) Inner-rate PID loop

The controller reads gyro rates omega from IMU and computes:

rate_error = omega - omega_des

For each axis, PID gives moment-like command M:

M = -(Kp*e + Ki*integral(e) + Kd\*de/dt) + cross_term

`cross_term` approximates rigid-body coupling due to inertia and rotation.

Then moments are scaled to motor-delta space with:

- `torque_to_speed_gain`

## 6) Motor mixing

For quad with 4 motors:

- Start from base speed (hover + throttle trim)
- Add roll/pitch/yaw deltas by fixed sign pattern

In code order:

- m0: +roll +pitch -yaw
- m1: -roll +pitch +yaw
- m2: -roll -pitch -yaw
- m3: +roll -pitch +yaw

Finally each motor is clamped to:

- `min_motor_speed` .. `max_motor_speed`

## 7) Safety behavior

Safety checks before control output:

- Deadman button must be pressed (`deadman_button`)
- Joystick must be recent (`joy_timeout_sec`)

If either fails, motor command is set to minimum for all motors.

## 8) Configuration files

The launch file loads three YAML files:

- `config/common_params.yaml`
- `config/attitude_params.yaml`
- `config/rate_params.yaml`

### 8.1 Common parameters (`common_params.yaml`)

- `imu_topic`: IMU topic name
- `joy_topic`: joystick topic name
- `motor_topic`: motor output topic name
- `publish_rate_hz`: control loop rate
- `motor_count`: expected number of motors (optimized for 4)
- `min_motor_speed`: lower clamp
- `max_motor_speed`: upper clamp
- `hover_motor_speed`: baseline speed around hover
- `throttle_trim_range`: max add/subtract around hover from throttle stick
- `throttle_deadzone`: small throttle region treated as zero
- `joy_timeout_sec`: max allowed age of joystick message
- `deadman_button`: index in Joy buttons array
- `axis_roll`: index in Joy axes array
- `axis_pitch`: index in Joy axes array
- `axis_yaw`: index in Joy axes array
- `axis_throttle`: index in Joy axes array

### 8.2 Attitude/SO(3) parameters (`attitude_params.yaml`)

- `attitude_inertia`: Ixx and Iyy estimate (kg\*m^2)
- `attitude_inertia_z`: Izz estimate (kg\*m^2)
- `K_R_attitude`: roll/pitch orientation-to-rate gain
- `K_R_yaw`: yaw orientation-to-rate gain
- `max_attitude_deg`: max commanded roll/pitch from full stick
- `yaw_gain`: fallback yaw stick scaling when IMU orientation is unavailable
- `torque_to_speed_gain`: scales computed moments to motor speed deltas

### 8.3 Rate PID parameters (`rate_params.yaml`)

Roll/pitch shared gains:

- `rate_Kp`
- `rate_Ki`
- `rate_Kd`

Yaw-specific gains:

- `rate_Kp_yaw`
- `rate_Ki_yaw`
- `rate_Kd_yaw`

Integral anti-windup settings:

- `rate_integral_limit`: maximum absolute size allowed for the stored integral term
- `rate_integral_leak_rate`: exponential decay rate applied to old integral error over time

## 9) Launch files

### `launch/drone_controller.launch.py`

Starts `drone_controller` with:

- namespace argument (`namespace`, default `drone`)
- optional topic overrides (`imu_topic`, `joy_topic`, `motor_topic`)
- parameters loaded from the three YAML files

Example:

```bash
ros2 launch drone_control drone_controller.launch.py
```

With overrides:

```bash
ros2 launch drone_control drone_controller.launch.py \
  namespace:=drone \
  imu_topic:=/drone/imu \
  joy_topic:=/joy \
  motor_topic:=/drone/command/motor_speed
```

### `launch/joy_gui.launch.py`

Starts a small Tk GUI node that publishes `sensor_msgs/msg/Joy`.
Useful when you do not have a physical joystick.

```bash
ros2 launch drone_control joy_gui.launch.py
```

## 10) How to tune in practice

Suggested order:

1. Verify axis mapping and deadman first
2. Set conservative `hover_motor_speed`, clamps, and throttle range
3. Tune rate PID (`rate_*`) with small attitude commands
4. Tune geometric gains (`K_R_attitude`, `K_R_yaw`)
5. Adjust `torque_to_speed_gain` to map moments to usable motor deltas

Symptoms and likely fixes:

- Slow response: increase `rate_Kp` or `K_R_attitude`
- Oscillation: reduce `rate_Kp` and/or `K_R_attitude`, increase `rate_Kd` slightly
- Steady offset: increase `rate_Ki` carefully
- Integral builds up too much: lower `rate_integral_limit`
- Controller remembers old errors too long: raise `rate_integral_leak_rate`
- Yaw unstable: lower `K_R_yaw` or yaw PID gains

## 11) Known assumptions and limits

- Mixer is explicitly for 4 motors.
- If `motor_count != 4`, controller publishes same base speed to all motors.
- Controller expects valid IMU quaternion + angular velocity.
- Parameters are updateable at runtime via ROS 2 parameter interface.

## 12) Source map

Main implementation:

- `src/drone_controller.cpp`

Support modules:

- `include/drone_control/utils.hpp`, `src/utils.cpp` (math helpers)
- `include/drone_control/rate_pid.hpp`, `src/rate_pid.cpp` (PID)
- `include/drone_control/mixer.hpp`, `src/mixer.cpp` (quad mixing)

Python tools:

- `scripts/joy_gui_publisher.py` (GUI Joy publisher)

If you want, the next step can be adding a one-page tuning playbook with specific starting ranges for each parameter and a step-by-step test script.
