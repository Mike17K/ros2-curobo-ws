cmake_minimum_required(VERSION 3.8)
project(testcpp)

# 1. Βρες τα πακέτα (Dependencies)
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)

# 2. Δημιούργησε το executable
add_executable(testcpp src/main.cpp)

# 3. Η "μαγική" εντολή - Συνδέει τα πάντα με μία κίνηση
ament_target_dependencies(testcpp
  rclcpp
)

# 4. Εγκατάσταση (για να δουλεύει το ros2 run)
install(TARGETS testcpp
  DESTINATION lib/${PROJECT_NAME})

ament_package()
