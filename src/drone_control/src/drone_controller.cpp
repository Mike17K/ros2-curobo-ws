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

namespace
{

constexpr double kPi = 3.14159265358979323846;

double clamp_value(double value, double lower, double upper)
{
  return std::max(lower, std::min(upper, value));
}

std::array<double, 3> quaternion_to_euler(
  double x, double y, double z, double w)
{
  const double sinr_cosp = 2.0 * (w * x + y * z);
  const double cosr_cosp = 1.0 - 2.0 * (x * x + y * y);
  const double roll = std::atan2(sinr_cosp, cosr_cosp);

  const double sinp = 2.0 * (w * y - z * x);
  double pitch = 0.0;
  if (std::abs(sinp) >= 1.0) {
    pitch = std::copysign(kPi / 2.0, sinp);
  } else {
    pitch = std::asin(sinp);
  }

  const double siny_cosp = 2.0 * (w * z + x * y);
  const double cosy_cosp = 1.0 - 2.0 * (y * y + z * z);
  const double yaw = std::atan2(siny_cosp, cosy_cosp);

  return {roll, pitch, yaw};
}

}  // namespace

class DroneController : public rclcpp::Node
{
public:
  explicit DroneController(const rclcpp::NodeOptions & options = rclcpp::NodeOptions())
  : Node("drone_controller", options)
  {
    imu_topic_ = declare_parameter<std::string>("imu_topic", "imu");
    joy_topic_ = declare_parameter<std::string>("joy_topic", "joy");
    motor_topic_ = declare_parameter<std::string>("motor_topic", "motor_speed");

    publish_rate_hz_ = declare_parameter<double>("publish_rate_hz", 50.0);
    motor_count_ = declare_parameter<int>("motor_count", 4);
    min_motor_speed_ = declare_parameter<double>("min_motor_speed", 0.0);
    max_motor_speed_ = declare_parameter<double>("max_motor_speed", 1000.0);
    hover_motor_speed_ = declare_parameter<double>("hover_motor_speed", 450.0);
    attitude_gain_ = declare_parameter<double>("attitude_gain", 120.0);
    deadman_button_ = declare_parameter<int>("deadman_button", 4);
    joy_timeout_sec_ = declare_parameter<double>("joy_timeout_sec", 0.5);
    axis_roll_ = declare_parameter<int>("axis_roll", 0);
    axis_pitch_ = declare_parameter<int>("axis_pitch", 1);
    axis_yaw_ = declare_parameter<int>("axis_yaw", 2);
    axis_throttle_ = declare_parameter<int>("axis_throttle", 3);

    const double timer_period_sec = publish_rate_hz_ > 0.0 ? (1.0 / publish_rate_hz_) : 0.02;

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

    const double throttle_norm = clamp_value((throttle_axis + 1.0) * 0.5, 0.0, 1.0);
    double base_speed = hover_motor_speed_ + throttle_norm * (max_motor_speed_ - hover_motor_speed_);
    base_speed = clamp_value(base_speed, min_motor_speed_, max_motor_speed_);

    double roll_correction = 0.0;
    double pitch_correction = 0.0;
    if (have_imu_) {
      const auto euler = quaternion_to_euler(
        last_imu_[0],
        last_imu_[1],
        last_imu_[2],
        last_imu_[3]);
      roll_correction = -euler[0] * attitude_gain_;
      pitch_correction = -euler[1] * attitude_gain_;
    }

    const double roll_term = roll_axis * attitude_gain_ + roll_correction;
    const double pitch_term = pitch_axis * attitude_gain_ + pitch_correction;
    const double yaw_term = yaw_axis * attitude_gain_;

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
      // Rotor order matches drone_description:
      // 0 = front left (ccw), 1 = rear right (ccw), 2 = front right (cw), 3 = rear left (cw)
      // Pitch correction must reduce the front pair and increase the rear pair when the drone
      // pitches nose-up, otherwise the controller will amplify a forward tip instead of damping it.
      motor_speeds = {
        clamp_value(base_speed - pitch_term + roll_term - yaw_term, min_motor_speed_, max_motor_speed_),
        clamp_value(base_speed + pitch_term - roll_term - yaw_term, min_motor_speed_, max_motor_speed_),
        clamp_value(base_speed - pitch_term - roll_term + yaw_term, min_motor_speed_, max_motor_speed_),
        clamp_value(base_speed + pitch_term + roll_term + yaw_term, min_motor_speed_, max_motor_speed_),
      };
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
  double hover_motor_speed_ {450.0};
  double attitude_gain_ {120.0};
  int deadman_button_ {4};
  double joy_timeout_sec_ {0.5};
  int axis_roll_ {0};
  int axis_pitch_ {1};
  int axis_yaw_ {2};
  int axis_throttle_ {3};

  std::array<double, 4> last_imu_ {};
  bool have_imu_ {false};
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