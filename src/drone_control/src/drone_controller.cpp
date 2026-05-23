#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <functional>
#include <memory>
#include <string>
#include <vector>

#include "actuator_msgs/msg/actuators.hpp"
#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/imu.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "rcl_interfaces/msg/set_parameters_result.hpp"

#include "drone_control/utils.hpp"
#include "drone_control/rate_pid.hpp"
#include "drone_control/mixer.hpp"

constexpr double kPi = 3.14159265358979323846;

class DroneController : public rclcpp::Node
{
public:
  explicit DroneController(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("drone_controller", options)
  {
    imu_topic_ = declare_parameter<std::string>("imu_topic", "/drone/imu");
    joy_topic_ = declare_parameter<std::string>("joy_topic", "joy");
    motor_topic_ = declare_parameter<std::string>("motor_topic", "/drone/command/motor_speed");

    publish_rate_hz_ = declare_parameter<double>("publish_rate_hz", 50.0);
    motor_count_ = declare_parameter<int>("motor_count", 4);
    min_motor_speed_ = declare_parameter<double>("min_motor_speed", 0.0);
    max_motor_speed_ = declare_parameter<double>("max_motor_speed", 1000.0);
    hover_motor_speed_ = declare_parameter<double>("hover_motor_speed", 505.0);
    deadman_button_ = declare_parameter<int>("deadman_button", 4);
    joy_timeout_sec_ = declare_parameter<double>("joy_timeout_sec", 0.5);
    axis_roll_ = declare_parameter<int>("axis_roll", 0);
    axis_pitch_ = declare_parameter<int>("axis_pitch", 1);
    axis_yaw_ = declare_parameter<int>("axis_yaw", 2);
    axis_throttle_ = declare_parameter<int>("axis_throttle", 3);

    // tuned inertia consistent with drone_description geometry (~0.017 kg*m^2)
    inertia_ = declare_parameter<double>("attitude_inertia", 0.017);  // kg*m^2 (approx)
    torque_to_speed_gain_ = declare_parameter<double>("torque_to_speed_gain", 0.7);
    max_attitude_deg_ = declare_parameter<double>("max_attitude_deg", 15.0);
    yaw_gain_ = declare_parameter<double>("yaw_gain", 20.0); // fallback mapping when IMU unavailable
    max_yaw_rate_deg_ = declare_parameter<double>("max_yaw_rate_deg", 90.0); // joystick -> yaw rate (deg/s)
    throttle_trim_range_ = declare_parameter<double>("throttle_trim_range", 80.0);
    throttle_deadzone_ = declare_parameter<double>("throttle_deadzone", 0.08);
    attitude_inertia_z_ = declare_parameter<double>("attitude_inertia_z", inertia_);

    // Geometric controller gains (SO(3))
    K_R_attitude_ = declare_parameter<double>("K_R_attitude", 8.0); // attitude gain (roll/pitch)
    K_R_yaw_ = declare_parameter<double>("K_R_yaw", 4.0); // yaw attitude gain

    // Rate PID inner-loop gains (roll/pitch share, yaw separate)
    rate_Kp_ = declare_parameter<double>("rate_Kp", 6.0);
    rate_Ki_ = declare_parameter<double>("rate_Ki", 0.1);
    rate_Kd_ = declare_parameter<double>("rate_Kd", 0.002);
    rate_Kp_yaw_ = declare_parameter<double>("rate_Kp_yaw", 4.0);
    rate_Ki_yaw_ = declare_parameter<double>("rate_Ki_yaw", 0.05);
    rate_Kd_yaw_ = declare_parameter<double>("rate_Kd_yaw", 0.001);
    rate_integral_limit_ = declare_parameter<double>("rate_integral_limit", 1.5);
    rate_integral_leak_rate_ = declare_parameter<double>("rate_integral_leak_rate", 0.5);

    // initialize rate PID controllers
    rate_pid_roll_.set_gains(rate_Kp_, rate_Ki_, rate_Kd_);
    rate_pid_pitch_.set_gains(rate_Kp_, rate_Ki_, rate_Kd_);
    rate_pid_yaw_.set_gains(rate_Kp_yaw_, rate_Ki_yaw_, rate_Kd_yaw_);
    rate_pid_roll_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);
    rate_pid_pitch_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);
    rate_pid_yaw_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);

    // Allow runtime tuning: update gains when relevant parameters change
    on_set_parameters_callback_handle_ = this->add_on_set_parameters_callback(
      [this](const std::vector<rclcpp::Parameter> & params) -> rcl_interfaces::msg::SetParametersResult {
        rcl_interfaces::msg::SetParametersResult result;
        result.successful = true;
        for (const auto & p : params) {
          const auto & name = p.get_name();
          if (name == "attitude_inertia") inertia_ = p.as_double();
          else if (name == "torque_to_speed_gain") torque_to_speed_gain_ = p.as_double();
          else if (name == "max_attitude_deg") max_attitude_deg_ = p.as_double();
          else if (name == "yaw_gain") yaw_gain_ = p.as_double();
          else if (name == "throttle_trim_range") throttle_trim_range_ = p.as_double();
          else if (name == "throttle_deadzone") throttle_deadzone_ = p.as_double();
          else if (name == "max_yaw_rate_deg") max_yaw_rate_deg_ = p.as_double();
          if (name == "K_R_attitude") K_R_attitude_ = p.as_double();
          else if (name == "K_R_yaw") K_R_yaw_ = p.as_double();
          else if (name == "attitude_inertia_z") attitude_inertia_z_ = p.as_double();
          else if (name == "rate_Kp") rate_Kp_ = p.as_double();
          else if (name == "rate_Ki") rate_Ki_ = p.as_double();
          else if (name == "rate_Kd") rate_Kd_ = p.as_double();
          else if (name == "rate_Kp_yaw") rate_Kp_yaw_ = p.as_double();
          else if (name == "rate_Ki_yaw") rate_Ki_yaw_ = p.as_double();
          else if (name == "rate_Kd_yaw") rate_Kd_yaw_ = p.as_double();
          else if (name == "rate_integral_limit") rate_integral_limit_ = p.as_double();
          else if (name == "rate_integral_leak_rate") rate_integral_leak_rate_ = p.as_double();
        }
        // apply gains to PID objects in case they were updated
        rate_pid_roll_.set_gains(rate_Kp_, rate_Ki_, rate_Kd_);
        rate_pid_pitch_.set_gains(rate_Kp_, rate_Ki_, rate_Kd_);
        rate_pid_yaw_.set_gains(rate_Kp_yaw_, rate_Ki_yaw_, rate_Kd_yaw_);
        rate_pid_roll_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);
        rate_pid_pitch_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);
        rate_pid_yaw_.set_integral_limits(rate_integral_limit_, rate_integral_leak_rate_);
        rate_pid_roll_.reset();
        rate_pid_pitch_.reset();
        rate_pid_yaw_.reset();
        return result;
      });

    const double timer_period_sec = publish_rate_hz_ > 0.0 ? (1.0 / publish_rate_hz_) : 0.02;
    control_dt_ = timer_period_sec;

    imu_subscription_ = create_subscription<sensor_msgs::msg::Imu>(
      imu_topic_, 10,
      std::bind(&DroneController::imu_callback, this, std::placeholders::_1));

    joy_subscription_ = create_subscription<sensor_msgs::msg::Joy>(
      joy_topic_, 10,
      std::bind(&DroneController::joy_callback, this, std::placeholders::_1));

    motor_publisher_ = create_publisher<actuator_msgs::msg::Actuators>(motor_topic_, 10);
    timer_ = create_wall_timer(
      std::chrono::duration<double>(timer_period_sec),
      std::bind(&DroneController::publish_command, this));

    RCLCPP_INFO(
      get_logger(),
      "Controller ready: imu=%s joy=%s motor=%s motors=%d",
      imu_topic_.c_str(), joy_topic_.c_str(), motor_topic_.c_str(), motor_count_);
  }

  void stop()
  {
    publish_zero_command("shutdown");
  }

private:
  void imu_callback(const sensor_msgs::msg::Imu::SharedPtr msg)
  {
    last_imu_[0] = msg->orientation.x;
    last_imu_[1] = msg->orientation.y;
    last_imu_[2] = msg->orientation.z;
    last_imu_[3] = msg->orientation.w;
    // store angular velocity for rate feedback
    last_gyro_[0] = msg->angular_velocity.x;
    last_gyro_[1] = msg->angular_velocity.y;
    last_gyro_[2] = msg->angular_velocity.z;
    have_imu_ = true;
  }

  void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg)
  {
    last_joy_axes_.assign(msg->axes.begin(), msg->axes.end());
    last_joy_buttons_.assign(msg->buttons.begin(), msg->buttons.end());
    last_joy_time_ = now();
  }

  double joy_axis(int index) const
  {
    if (index < 0 || index >= static_cast<int>(last_joy_axes_.size())) {
      return 0.0;
    }
    return static_cast<double>(last_joy_axes_[static_cast<std::size_t>(index)]);
  }

  int joy_button(int index) const
  {
    if (index < 0 || index >= static_cast<int>(last_joy_buttons_.size())) {
      return 0;
    }
    return last_joy_buttons_[static_cast<std::size_t>(index)];
  }

  void publish_zero_command(const char * reason)
  {
    RCLCPP_DEBUG(get_logger(), "Zeroing motors: %s", reason);
    actuator_msgs::msg::Actuators command;
    command.velocity.assign(static_cast<std::size_t>(std::max(motor_count_, 0)), min_motor_speed_);
    motor_publisher_->publish(command);
  }

  void publish_command()
  {
    const rclcpp::Duration joy_timeout = rclcpp::Duration::from_seconds(joy_timeout_sec_);
    if ((now() - last_joy_time_) > joy_timeout) {
      publish_zero_command("joy timeout");
      return;
    }

    if (joy_button(deadman_button_) == 0) {
      publish_zero_command("deadman not pressed");
      return;
    }

    const double throttle_axis = joy_axis(axis_throttle_);
    const double roll_axis = joy_axis(axis_roll_);
    const double pitch_axis = joy_axis(axis_pitch_);
    const double yaw_axis = joy_axis(axis_yaw_);

    double throttle_command = throttle_axis;
    if (std::fabs(throttle_command) < throttle_deadzone_) {
      throttle_command = 0.0;
    }
    const double throttle_trim = drone_control::clamp_value(throttle_command, -1.0, 1.0) * throttle_trim_range_;
    double base_speed = hover_motor_speed_ + throttle_trim;
    base_speed = drone_control::clamp_value(base_speed, min_motor_speed_, max_motor_speed_);

    // Attitude control (roll and pitch)
    double roll_delta = 0.0;
    double pitch_delta = 0.0;
    double yaw_term = yaw_axis * yaw_gain_;
    if (have_imu_) {
      const auto euler = drone_control::quaternion_to_euler(
        last_imu_[0], last_imu_[1], last_imu_[2], last_imu_[3]);

      const double desired_roll = roll_axis * (max_attitude_deg_ * kPi / 180.0);
      const double desired_pitch = pitch_axis * (max_attitude_deg_ * kPi / 180.0);
      const double roll_rate = last_gyro_[0];
      const double pitch_rate = last_gyro_[1];

      // Geometric (SO(3)) attitude control using utils
      auto R = drone_control::R_from_quat(last_imu_);
      const double current_yaw = euler[2];
      // Keep the attitude reference aligned with the current yaw frame.
      // Yaw is controlled separately as a rate, so it should not distort roll/pitch correction.
      auto Rd = drone_control::mat_mul(drone_control::Rz(current_yaw),
                   drone_control::mat_mul(drone_control::Ry(desired_pitch),
                          drone_control::Rx(desired_roll)));

      auto RdT = drone_control::mat_transpose(Rd);
      auto RT = drone_control::mat_transpose(R);
      auto temp1 = drone_control::mat_mul(RdT, R);
      auto temp2 = drone_control::mat_mul(RT, Rd);
      std::array<std::array<double,3>,3> diff{};
      for (int i=0;i<3;++i) for (int j=0;j<3;++j) diff[i][j] = temp1[i][j] - temp2[i][j];
      auto eR = drone_control::vee(diff);
      eR[0] *= 0.5; eR[1] *= 0.5; eR[2] *= 0.5;

      // measured angular velocity
      std::array<double,3> omega = {roll_rate, pitch_rate, last_gyro_[2]};

      // Outer-loop: desired body rates from attitude error (roll/pitch)
      std::array<double,3> omega_des{};
      omega_des[0] = K_R_attitude_ * eR[0];
      omega_des[1] = K_R_attitude_ * eR[1];
      // For yaw, joystick commands map to a desired angular velocity (rad/s)
      const double desired_yaw_rate = yaw_axis * (max_yaw_rate_deg_ * kPi / 180.0);
      omega_des[2] = desired_yaw_rate;

      // Inertia and Coriolis-like cross term
      double Ixx = inertia_;
      double Iyy = inertia_;
      double Izz = attitude_inertia_z_;
      std::array<double,3> cross{
        omega[1]*omega[2]*(Iyy - Izz),
        omega[2]*omega[0]*(Izz - Ixx),
        omega[0]*omega[1]*(Ixx - Iyy)
      };

      // Inner-loop: rate PID -> moments (use RatePID objects)
      std::array<double,3> rate_err{};
      for (int i=0;i<3;++i) rate_err[i] = omega[i] - omega_des[i];

      double Mx = -rate_pid_roll_.update(rate_err[0], control_dt_) + cross[0];
      double My = -rate_pid_pitch_.update(rate_err[1], control_dt_) + cross[1];
      double Mz = -rate_pid_yaw_.update(rate_err[2], control_dt_) + cross[2];

      roll_delta = Mx * torque_to_speed_gain_;
      pitch_delta = My * torque_to_speed_gain_;
      yaw_term = Mz * torque_to_speed_gain_;
    }

    std::vector<double> motor_speeds;
    if (motor_count_ != 4) {
      if (!warned_non_quad_) {
        RCLCPP_WARN(
          get_logger(),
          "motor_count=%d is not 4, publishing base speed to all outputs",
          motor_count_);
        warned_non_quad_ = true;
      }
      motor_speeds.assign(static_cast<std::size_t>(std::max(motor_count_, 0)), base_speed);
    } else {
      auto mixed = drone_control::quad_mix(base_speed, roll_delta, pitch_delta, yaw_term);
      motor_speeds.resize(4);
      for (size_t i=0;i<4;++i) {
        motor_speeds[i] = drone_control::clamp_value(mixed[i], min_motor_speed_, max_motor_speed_);
      }
    }

    actuator_msgs::msg::Actuators command;
    command.velocity = motor_speeds;
    motor_publisher_->publish(command);
  }

  std::string imu_topic_;
  std::string joy_topic_;
  std::string motor_topic_;

  double publish_rate_hz_ {50.0};
  int motor_count_ {4};
  double min_motor_speed_ {0.0};
  double max_motor_speed_ {1000.0};
  double hover_motor_speed_ {505.0};
  int deadman_button_ {4};
  double joy_timeout_sec_ {0.5};
  int axis_roll_ {0};
  int axis_pitch_ {1};
  int axis_yaw_ {2};
  int axis_throttle_ {3};
  // IMU state
  std::array<double, 4> last_imu_ {};
  std::array<double, 3> last_gyro_ {};
  bool have_imu_ {false};
  // inertia
  double inertia_ {0.02};
  double torque_to_speed_gain_ {0.5};
  double max_attitude_deg_ {30.0};
  double yaw_gain_ {50.0};
  double throttle_trim_range_ {80.0};
  double throttle_deadzone_ {0.08};
  // Geometric controller gains
  double K_R_attitude_ {8.0};
  double K_R_yaw_ {4.0};
  double attitude_inertia_z_ {0.02};
  // Rate PID inner-loop gains and state
  double rate_Kp_ {6.0};
  double rate_Ki_ {0.1};
  double rate_Kd_ {0.002};
  double rate_Kp_yaw_ {4.0};
  double rate_Ki_yaw_ {0.05};
  double rate_Kd_yaw_ {0.001};
  double rate_integral_limit_ {1.5};
  double rate_integral_leak_rate_ {0.5};
  double max_yaw_rate_deg_ {90.0};
  drone_control::RatePID rate_pid_roll_;
  drone_control::RatePID rate_pid_pitch_;
  drone_control::RatePID rate_pid_yaw_;
  double control_dt_ {0.02};
  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr on_set_parameters_callback_handle_ {nullptr};
  std::vector<float> last_joy_axes_;
  std::vector<std::int32_t> last_joy_buttons_;
  rclcpp::Time last_joy_time_ {0, 0, RCL_ROS_TIME};
  bool warned_non_quad_ {false};

  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr imu_subscription_;
  rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr joy_subscription_;
  rclcpp::Publisher<actuator_msgs::msg::Actuators>::SharedPtr motor_publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char * argv[])
{
  rclcpp::init(argc, argv);
  auto node = std::make_shared<DroneController>();
  rclcpp::spin(node);
  node->stop();
  rclcpp::shutdown();
  return 0;
}