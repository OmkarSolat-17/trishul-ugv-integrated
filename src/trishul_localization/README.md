# trishul_localization

> **Owner**: Localization Lead  
> **Status**: ⚠️ Placeholder (Package Not Yet Initialized)

## Scope & Purpose
This package will house spatial mapping and state estimation:
- Odometry fusion configurations (e.g., Extended Kalman Filter via `robot_localization`).
- Visual SLAM / Visual Odometry nodes or configurations.
- Map generation and saving configurations.
- TF frame broadcasting for `map -> odom -> base_link`.

## Future Package Initialization
When ready to implement, initialize this package using `ros2 pkg create`:
```bash
cd <workspace_root>
ros2 pkg create --build-type ament_cmake trishul_localization --dependencies rclcpp nav_msgs geometry_msgs tf2 tf2_ros
```
*Note: Do not create manual empty `package.xml` or `CMakeLists.txt` files before running the standard tool.*
