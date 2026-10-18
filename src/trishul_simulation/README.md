# trishul_simulation

> **Owner**: Simulation Lead  
> **Status**: ⚠️ Placeholder (Package Not Yet Initialized)

## Scope & Purpose
This package will house the Gazebo Harmonic simulation components:
- Gazebo outdoor world SDF files (terrain, obstacles, sun/lighting).
- Gazebo Sim spawn launch scripts.
- `ros_gz_bridge` parameter and mapping YAML files (bridging Gazebo clock, camera images, and control topics to ROS 2).
- Simulated sensor plugins configuration.

## Future Package Initialization
When ready to implement, initialize this package using `ros2 pkg create` from the workspace root:
```bash
cd <workspace_root>
ros2 pkg create --build-type ament_cmake trishul_simulation --dependencies rclcpp ros_gz_sim ros_gz_bridge ros_gz_image
```
*Note: Do not create manual empty `package.xml` or `CMakeLists.txt` files before running the standard tool.*
