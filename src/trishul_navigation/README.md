# trishul_navigation

> **Owner**: Navigation Lead  
> **Status**: In Active Development

## Scope & Purpose
This package houses Nav2 configuration, autonomous waypoint navigation, active obstacle safety braking, and sensor monitoring for the Trishul UGV:
- `launch/navigation.launch.py`: Unified bringup launching Gazebo simulation, Nav2 stack with Trishul parameters, RViz2, and monitoring nodes.
- `mission_navigator`: Autonomous mission commander using Nav2 Simple Commander API. Sends high-level waypoint goals (reconnaissance checkpoints), monitors ETA, and handles task recovery without requiring GUI clicking.
- `sensor_monitor`: Active safety supervisor. Subscribes to `/scan` (LiDAR), evaluates proximity danger thresholds (`DANGER` < 0.25m, `WARNING` < 0.50m, `CLEAR`), and automatically publishes an emergency stop to `/cmd_vel` if a collision is imminent in the forward arc.
- `status_node`: Periodic 1 Hz heartbeat publisher on `trishul/status`.
- `config/nav2_params.yaml`: Nav2 stack parameterization (costmaps, planners, AMCL, controllers).
- `rviz/trishul_nav.rviz`: RViz2 layout configured for Trishul navigation displays.

## Usage

### 1. Build & Source
```bash
colcon build --packages-select trishul_navigation
source install/setup.bash
```

### 2. Launch Unified Navigation Simulation
```bash
# Launches Gazebo (GUI), Nav2, RViz, sensor_monitor, and status_node together:
ros2 launch trishul_navigation navigation.launch.py
```

### 3. Run Autonomous Mission (High-Level Instructions)
In a new terminal:
```bash
source install/setup.bash
ros2 run trishul_navigation mission_navigator
```
The robot will autonomously navigate through checkpoint waypoints without requiring manual 2D pose estimates or mouse-clicking goals.

### 4. Active Safety Controller
The `sensor_monitor` node runs automatically with the launch file and monitors LiDAR readings. If an obstacle appears within 0.25 m in front of the vehicle, it issues an immediate emergency brake on `/cmd_vel`.

## Running Tests
```bash
colcon test --packages-select trishul_navigation
colcon test-result --all
```
