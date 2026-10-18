# trishul_description

> **Owner**: Simulation Lead  
> **Status**: ⚠️ Placeholder (Package Not Yet Initialized)

## Scope & Purpose
This package will house the robot's physical and kinematic description:
- Robot URDF / Xacro macro definitions.
- Visual and collision meshes (STL / DAE / OBJ).
- Physical properties: masses, centers of mass, and inertial tensors.
- Sensor mount locations and joint definitions per REP-103 and REP-105.

## Future Package Initialization
When ready to implement, initialize this package using `ros2 pkg create` from the workspace root:
```bash
cd <workspace_root>
ros2 pkg create --build-type ament_cmake trishul_description --dependencies urdf xacro
```
*Note: Do not create manual empty `package.xml` or `CMakeLists.txt` files before running the standard tool.*
