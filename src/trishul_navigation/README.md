# Trishul Navigation (`trishul_navigation`)

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-blue.svg)](https://docs.ros.org/en/jazzy/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build & Test](https://img.shields.io/badge/Tests-0_Errors_|_Passing-success.svg)](#running-tests)
[![Package Status](https://img.shields.io/badge/Status-Fully_Functional-brightgreen.svg)](#)

> **Subsystem**: Autonomous Navigation & Guidance  
> **Lead**: Navigation Lead (`trishul-navigation` branch)  
> **Target Robot**: Trishul Autonomous Unmanned Ground Vehicle (UGV)

---

## 1. System Overview

`trishul_navigation` is the central navigation and guidance package for the Trishul UGV platform. It integrates Nav2 path planning, costmap management, active LiDAR proximity supervision, autonomous mission sequencing, and pre-configured RViz2 visualizations into a unified, reproducible system.

```
                    +------------------------------------+
                    |       Gazebo Sim (Physics & LiDAR) |
                    +------------------+-----------------+
                                       | /scan, /clock, /tf
                                       v
+--------------------------------------+--------------------------------------+
|                           trishul_navigation                                |
|                                                                             |
|  +--------------------+    +--------------------+    +--------------------+ |
|  | mission_navigator  |    |   sensor_monitor   |    |    status_node     | |
|  | - Autonomous Goals |    | - LiDAR Sectors    |    | - 1 Hz Heartbeat   | |
|  | - ETA & Progress   |    | - Active Emergency |    | - Telemetry        | |
|  | - Custom (X, Y)    |    |   Collision Brake  |    |   Health           | |
|  +---------+----------+    +---------+----------+    +---------+----------+ |
|            |                         |                         |            |
|            | Action: NavToPose       | /cmd_vel (Emergency)    |            |
|            v                         v                         v            |
|  +-----------------------------------------------------------------------+  |
|  |                               Nav2 Stack                              |  |
|  |   - AMCL Self-Localization (Auto Spawn Alignment: X=-2.00, Y=-0.50)   |  |
|  |   - Global Costmap & Smac/NavFn Planners                             |  |
|  |   - Local Costmap & DWB/MPPI Trajectory Controllers                   |  |
|  |   - Robust WSL Transform Tolerances (1.5s tolerance, 1000ms BT ack)   |  |
|  +-----------------------------------+-----------------------------------+  |
+--------------------------------------|--------------------------------------+
                                       | Displays: Map, Costmaps, Paths, Scans
                                       v
                    +------------------------------------+
                    |          RViz 2 Interface          |
                    |   (trishul_nav.rviz pre-profile)   |
                    +------------------------------------+
```

---

## 2. Key Capabilities Implemented

### 🚀 Unified Single-Command Launch (`navigation.launch.py`)
Brings up the entire simulation environment in one terminal:
* Launches Gazebo Sim with the environment and robot model.
* Boots the full Nav2 navigation stack configured with Trishul parameters.
* Automatically launches RViz2 loaded with the `trishul_nav.rviz` display profile.
* Launches the active `sensor_monitor` and `status_node` background supervisors.

### 🎯 Automatic AMCL Self-Localization (Zero-Click Startup)
In traditional setups, operators must manually click "2D Pose Estimate" in RViz. In `trishul_navigation`:
* `amcl` is configured with `set_initial_pose: true` aligned with the exact Gazebo spawn coordinates (`X = -2.00, Y = -0.50, Yaw = 0.00`).
* The robot initializes and localizes itself automatically on startup without mouse intervention.

### 🛡️ Active Collision Prevention & Emergency Braking (`sensor_monitor`)
Unlike passive monitoring scripts that only print text, `sensor_monitor` actively defends the vehicle:
* Filters and segments `/scan` LiDAR readings into angular sectors (`FRONT`, `FRONT-LEFT`, `LEFT`, `FRONT-RIGHT`, `RIGHT`, `OTHER`).
* Evaluates proximity thresholds (`DANGER` < 0.25 m, `WARNING` < 0.50 m, `CLEAR`).
* **Active Safety Brake**: If an obstacle breaches the forward arc (< 0.25 m), it automatically issues an **Emergency Stop command (`linear.x = 0.0`)** to `/cmd_vel` to prevent hardware collisions.

### 🗺️ Autonomous Mission Commander (`mission_navigator`)
* Programmatic mission control built on the **Nav2 Simple Commander API** (`BasicNavigator`).
* Enables hands-free autonomous traversal across the arena without needing to click goals in RViz.
* Supports **custom target coordinates** passed directly from the terminal.
* Synchronized with simulation time (`use_sim_time:=true`) to avoid clock-drift bugs.

### ⚡ WSL-Tuned Real-Time Tolerances
Configured specifically to prevent false transform aborts in virtualized and WSL2 environments:
* `transform_tolerance: 1.5s` (increased from 0.1s to absorb virtualization scheduling jitter).
* `default_server_timeout: 1000ms` (increased from 20ms to allow smooth planner acknowledgement).
* `source_timeout: 2.0s` for collision monitoring.

---

## 3. Package Structure

```
trishul_navigation/
├── CMakeLists.txt / setup.py     # Build configuration and install targets
├── setup.cfg                     # Executable script packaging rules
├── package.xml                   # Package manifest with ROS 2 dependencies
├── README.md                     # Comprehensive package documentation
├── config/
│   └── nav2_params.yaml          # Nav2 parameterization (costmaps, planners, AMCL, controllers)
├── rviz/
│   └── trishul_nav.rviz          # Saved RViz2 display profile for Trishul UGV
├── launch/
│   └── navigation.launch.py      # Master launch file
├── trishul_navigation/
│   ├── __init__.py
│   ├── mission_navigator.py      # Autonomous mission & waypoint commander node
│   ├── sensor_monitor.py         # Active LiDAR sector & emergency safety brake node
│   └── status_node.py            # Continuous 1 Hz system telemetry heartbeat node
└── test/
    ├── test_copyright.py         # Copyright test
    ├── test_flake8.py            # PEP8 & Flake8 linter test
    └── test_pep257.py            # Docstring conventions test
```

---

## 4. Quick Start & Execution Guide

### Prerequisites
* OS: Ubuntu 24.04 LTS (native or WSL2)
* ROS 2 Distribution: **Jazzy Jalisco**
* Packages: `nav2_bringup`, `nav2_simple_commander`, `ros_gz_sim`, `rviz2`

### Step 1: Build & Source Workspace
From your workspace root:
```bash
cd ~/trishul_ugv
colcon build --symlink-install --packages-select trishul_navigation
source install/setup.bash
```

---

### Step 2: Launch the Navigation System
In your first terminal:
```bash
ros2 launch trishul_navigation navigation.launch.py
```
This boots Gazebo, Nav2, RViz, and background monitoring nodes simultaneously.

---

### Step 3: Command the UGV Where to Go

Choose any of the following control methods:

#### Method A: Autonomous Cross-Arena Mission (Terminal)
In a second terminal, command the robot to autonomously navigate across the arena to the opposite end (`x = 1.80, y = -0.50`):
```bash
cd ~/trishul_ugv
source install/setup.bash
ros2 run trishul_navigation mission_navigator
```

#### Method B: Send Any Custom (X, Y) Coordinates (Terminal)
Command the robot to drive to specific coordinates of your choice:
```bash
# Example: Send the robot to Coordinate X = 1.0, Y = 0.5
ros2 run trishul_navigation mission_navigator --ros-args -p target_x:=1.0 -p target_y:=0.5
```

#### Method C: Visual Point-and-Click (RViz GUI)
1. In the top toolbar of RViz, click the **`Nav2 Goal`** button.
2. Click on any open floor space on the map and drag the green orientation arrow.
3. Release the mouse button — Nav2 plans the path and drives immediately.

#### Method D: Manual Keyboard Teleoperation (Manual WASD Driving)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```
*(Your active `sensor_monitor` node remains alive in the background and will trigger emergency stops if you drive too close to obstacles).*

---

## 5. Topic & Interface Specification

| Topic / Service | Interface Type | Direction | Description |
| :--- | :--- | :--- | :--- |
| `/scan` | `sensor_msgs/msg/LaserScan` | Input | 2D LiDAR range scan feed. |
| `/clock` | `rosgraph_msgs/msg/Clock` | Input | Simulation clock synchronized with Gazebo. |
| `/odom` | `nav_msgs/msg/Odometry` | Input | Wheel odometry state. |
| `/initialpose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | Input/Output | AMCL localization initialization topic. |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Output | Velocity commands sent to motors / simulation. |
| `trishul/status` | `std_msgs/msg/String` | Output | 1 Hz continuous telemetry heartbeat message. |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Action | Nav2 high-level navigation action server. |

---

## 6. Parameters & Tuning Reference

| Node / Component | Parameter | Default | Description |
| :--- | :--- | :--- | :--- |
| `amcl` | `set_initial_pose` | `true` | Automatically aligns localized pose on launch. |
| `amcl` | `initial_pose.x / y` | `-2.00 / -0.50` | Default spawn coordinates matching Gazebo. |
| `amcl` | `transform_tolerance` | `1.5` | Maximum allowable transform latency (seconds). |
| `bt_navigator` | `default_server_timeout` | `1000` | Milliseconds allowed for action acknowledgment. |
| `trishul_sensor_monitor` | `danger_distance` | `0.25` | Distance threshold (m) that triggers Emergency Stop. |
| `trishul_sensor_monitor` | `warning_distance` | `0.50` | Proximity warning threshold (m). |
| `trishul_mission_navigator`| `target_x / target_y` | `1.80 / -0.50` | Autonomous cross-arena destination coordinate. |

---

## 7. Quality Assurance & Tests

The package strictly adheres to team quality standards:
* **Flake8 (PEP8)**: Pass (Clean indentation, import ordering, and line length limits).
* **PEP257**: Pass (Standard Python docstrings).
* **colcon test results**:
  ```text
  Summary: 3 tests, 0 errors, 0 failures, 1 skipped (copyright)
  ```

To run tests locally:
```bash
colcon test --packages-select trishul_navigation
colcon test-result --all --verbose
```
