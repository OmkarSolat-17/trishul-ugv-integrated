# trishul_navigation

> **Owner**: Navigation Lead  
> **Status**: ⚠️ Placeholder (Package Not Yet Initialized)

## Scope & Purpose
This package will house Nav2 configuration and autonomous navigation pipelines:
- Nav2 parameter files (`nav2_params.yaml`) configuring global/local costmaps, planners, and controllers.
- Custom Behavior Trees (BT XML) for recovery, retry, and waypoint following.
- Costmap obstacle and inflation layer configurations utilizing vision/perception feeds.
- Navigation launch scripts.

## Future Package Initialization
When ready to implement, initialize this package using `ros2 pkg create`:
```bash
cd <workspace_root>
ros2 pkg create --build-type ament_cmake trishul_navigation --dependencies rclcpp nav2_bringup nav2_msgs geometry_msgs
```
*Note: Do not create manual empty `package.xml` or `CMakeLists.txt` files before running the standard tool.*
