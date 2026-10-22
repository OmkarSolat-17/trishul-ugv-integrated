# trishul_navigation

> **Owner**: Navigation Lead  
> **Status**: In Active Development

## Scope & Purpose
This package houses Nav2 configuration, autonomous navigation pipelines, and sensor monitoring nodes for the Trishul UGV:
- `launch/navigation.launch.py`: Unified bringup launching Gazebo simulation, Nav2 stack with Trishul parameters, RViz2, and custom monitoring nodes.
- `config/nav2_params.yaml`: Nav2 stack parameterization (costmaps, planners, AMCL, controllers).
- `rviz/trishul_nav.rviz`: RViz2 layout configured for Trishul navigation displays.
- `sensor_monitor`: Subscribes to `/scan` (LiDAR) to evaluate proximity danger thresholds (`DANGER` < 0.25m, `WARNING` < 0.50m, `CLEAR`) and angular sectors (`FRONT`, `LEFT`, `RIGHT`, etc.).
- `status_node`: Periodic 1 Hz heartbeat publisher on `trishul/status`.

## Usage

### 1. Build & Source
```bash
colcon build --packages-select trishul_navigation
source install/setup.bash
```

### 2. Launch Unified Navigation System
```bash
# Launches Gazebo, Nav2, RViz, sensor_monitor, and status_node together:
ros2 launch trishul_navigation navigation.launch.py
```

### 3. Run Standalone Nodes
```bash
# Run sensor monitor individually:
ros2 run trishul_navigation sensor_monitor

# Run status node individually:
ros2 run trishul_navigation status_node
```

## Running Tests
```bash
colcon test --packages-select trishul_navigation
colcon test-result --all
```
