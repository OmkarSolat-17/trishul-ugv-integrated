# Trishul Navigation (`trishul_navigation`)

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-blue.svg)](https://docs.ros.org/en/jazzy/)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build & Test](https://img.shields.io/badge/Tests-0_Errors_|_Passing-success.svg)](#7-quality-assurance--testing)
[![Package Status](https://img.shields.io/badge/Status-Fully_Operational-brightgreen.svg)](#)

> **Subsystem**: Autonomous Navigation & Guidance  
> **Lead**: Navigation Lead (`trishul-navigation` branch)  
> **Target Robot**: Trishul Autonomous Unmanned Ground Vehicle (UGV)  
> **Target Environment**: Gazebo Harmonic / ROS 2 Jazzy on WSL2 (Ubuntu 24.04 LTS)

---

## 1. System Overview & Architecture

`trishul_navigation` is the central navigation and guidance subsystem for the Trishul UGV platform. It integrates global and local path planning (Nav2), costmap management, active LiDAR proximity supervision with emergency collision braking, autonomous mission sequencing, and pre-configured RViz 2 visualizations into a unified, production-ready system.

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
|  |   - Global Costmap (Static & Obstacle Inflation Layers)               |  |
|  |   - Local Costmap (Dynamic Rolling Window & Voxel/Scan Clearing)      |  |
|  |   - Smac / NavFn Global Path Planner                                  |  |
|  |   - DWB / MPPI Local Trajectory Controller                            |  |
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

### 🚀 1. Unified Single-Command Launch (`navigation.launch.py`)
Brings up the entire simulation environment in a single command:
* Launches Gazebo Sim with the environment and robot model.
* Boots the full Nav2 navigation stack (AMCL, Planner Server, Controller Server, BT Navigator, Costmaps, Lifecycle Manager).
* Automatically launches RViz 2 pre-loaded with the `trishul_nav.rviz` display profile.
* Starts background safety monitoring (`sensor_monitor`) and telemetry heartbeat (`status_node`).

### 🎯 2. Automatic AMCL Self-Localization (Zero-Click Startup)
In standard setups, an operator must manually click "2D Pose Estimate" in RViz. In `trishul_navigation`:
* `amcl` is configured with `set_initial_pose: true` aligned with the exact Gazebo spawn coordinates (`X = -2.00, Y = -0.50, Yaw = 0.00`).
* Eliminates the default `(0, 0)` center-pillar collision bug in `turtlebot3_world`.
* The robot initializes and localizes itself automatically on startup without any mouse intervention.

### 🛡️ 3. Active Collision Prevention & Emergency Braking (`sensor_monitor`)
Unlike passive monitoring scripts that only print text, `sensor_monitor` actively defends the vehicle:
* Divides `/scan` LiDAR readings into angular sectors (`FRONT`, `FRONT-LEFT`, `LEFT`, `FRONT-RIGHT`, `RIGHT`).
* Evaluates proximity thresholds (`DANGER < 0.25 m`, `WARNING < 0.50 m`, `CLEAR`).
* **Active Safety Brake**: If an obstacle breaches the forward arc (< 0.25 m), it automatically publishes an **Emergency Stop command (`linear.x = 0.0`)** to `/cmd_vel` to prevent hardware collisions.

### 🗺️ 4. Autonomous Mission Commander (`mission_navigator`)
* Programmatic mission control built on the **Nav2 Simple Commander API** (`BasicNavigator`).
* Enables hands-free autonomous traversal across the arena without needing to click goals in RViz.
* Supports **custom target coordinates** passed directly from the terminal via `-p target_x:=... -p target_y:=...`.
* Synchronized with simulation time (`use_sim_time:=true`) to avoid clock-drift bugs.
* Provides real-time ETA, distance remaining, and recovery tracking.

### ⚡ 5. WSL2 Real-Time Tolerances & Stability Fixes
Configured specifically to prevent false transform aborts and timeouts in virtualized and WSL2 environments:
* `transform_tolerance: 1.5s` (increased from 0.1s to absorb virtualization scheduling jitter).
* `default_server_timeout: 1000ms` in `bt_navigator` (increased from 20ms to allow smooth planner acknowledgement).
* `source_timeout: 2.0s` for collision monitoring.

---

## 3. Package Structure

```text
src/trishul_navigation/
├── package.xml                   # Package manifest with ROS 2 dependencies
├── setup.py                      # Build configuration and console entry points
├── setup.cfg                     # Executable script packaging rules
├── README.md                     # Comprehensive package documentation (this file)
├── config/
│   └── nav2_params.yaml          # Nav2 parameterization (costmaps, planners, AMCL, controllers)
├── rviz/
│   └── trishul_nav.rviz          # Saved RViz 2 display layout for Trishul UGV
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
From the workspace root (`~/trishul_ugv`):
```bash
cd ~/trishul_ugv
colcon build --symlink-install --packages-select trishul_navigation
source install/setup.bash
```

> **Why `colcon`?** ROS 2 uses `colcon` (collective construction) instead of standard Python `pip` because a ROS workspace contains multiple interconnected packages with distinct dependencies and build types (C++ `ament_cmake` and Python `ament_python`). `colcon` resolves package dependencies in topological order, performs out-of-source builds, and creates symlink environments (`--symlink-install`) so Python code edits are reflected immediately without re-compiling.

---

### Step 2: Launch the Navigation System
In Terminal 1:
```bash
cd ~/trishul_ugv
source install/setup.bash
ros2 launch trishul_navigation navigation.launch.py
```
This single command boots Gazebo Sim, Nav2, RViz 2, and background monitoring nodes simultaneously.

---

### Step 3: Command the Robot Where to Go

Choose any of the following control methods:

#### Method A: Autonomous Cross-Arena Mission (Terminal)
In Terminal 2, command the robot to autonomously navigate across the arena to the opposite end (`x = 1.80, y = -0.50`):
```bash
cd ~/trishul_ugv
source install/setup.bash
ros2 run trishul_navigation mission_navigator
```

#### Method B: Send Any Custom (X, Y) Coordinates (Terminal)
Command the robot to drive to specific coordinates of your choice:
```bash
# Example 1: Navigate to coordinate X = 1.0, Y = 0.5
ros2 run trishul_navigation mission_navigator --ros-args -p target_x:=1.0 -p target_y:=0.5

# Example 2: Navigate to coordinate X = -0.5, Y = 1.2 with custom heading (yaw = 1.57 rad)
ros2 run trishul_navigation mission_navigator --ros-args -p target_x:=-0.5 -p target_y:=1.2 -p target_yaw:=1.57
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

## 5. Engineering Problem Solving & Bug Fixes

During the development of this subsystem, several critical real-world robotics and virtualization challenges were identified and systematically resolved:

### 1. Gazebo vs. RViz Initial Pose Mismatch (The Center Pillar Bug)
* **Problem**: In `turtlebot3_world`, 9 pillars exist at $X, Y \in \{-1.1, 0, 1.1\}$. The center pillar is at $(0.0, 0.0)$. AMCL without an initial pose defaulted to $(0.0, 0.0)$, placing the robot on top of a solid obstacle in RViz while Gazebo had spawned it at $(-2.00, -0.50)$.
* **Root Cause**: Uninitialized AMCL filter defaulting to origin $(0, 0)$.
* **Resolution**: In `nav2_params.yaml`, configured `set_initial_pose: true` with `initial_pose: {x: -2.00, y: -0.50, yaw: 0.0}` matching the Gazebo spawn coordinates. Also added initial pose initialization in `mission_navigator.py`.

### 2. WSL2 Transform Extrapolation & Timing Jitter
* **Problem**: Nav2 aborted navigation with: `Transform data too old when converting from map to odom`.
* **Root Cause**: WSL2 runs inside a virtualized hypervisor. Minor CPU scheduling latency (0.2–0.3s) exceeded Nav2's default `transform_tolerance: 0.1s`.
* **Resolution**: Increased `transform_tolerance` to `1.5s` across AMCL, global costmap, local costmap, planner, and controller. Increased `source_timeout` in collision monitor to `2.0s`.

### 3. Behavior Tree Action Server Timeout (0.07s Failure)
* **Problem**: Nav2 aborted path computation with: `Timed out while waiting for action server to acknowledge goal request for compute_path_to_pose`.
* **Root Cause**: In Nav2 Jazzy source (`bt_action_server_impl.hpp:169`), `default_server_timeout` is measured in **milliseconds**. The initial configuration had `default_server_timeout: 20` (20 ms!), causing immediate timeouts when computing paths across the arena.
* **Resolution**: Increased `default_server_timeout` to `1000` (1000 ms / 1 second), providing ample window for planner acknowledgment.

### 4. Lifecycle Server Shutdown Bug
* **Problem**: After running `mission_navigator`, RViz could no longer accept goals because Nav2 servers disappeared.
* **Root Cause**: `mission_navigator.py` was calling `navigator.lifecycleShutdown()`, which transitioned Nav2 servers to the `finalized` (dead) state.
* **Resolution**: Removed `lifecycleShutdown()`; the script now cleanly calls `navigator.destroy_node()`, leaving Nav2 servers running for subsequent commands.

---

## 6. Topic & Interface Specification

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

## 7. Parameters & Tuning Reference

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

## 8. Quality Assurance & Testing

The package strictly adheres to ROS 2 standard quality practices:
* **Flake8 (PEP8)**: Pass (Clean indentation, import ordering, line lengths).
* **PEP257**: Pass (Standard Python docstrings).
* **colcon test results**:
  ```text
  Starting >>> trishul_navigation
  Finished <<< trishul_navigation [1.16s]

  Summary: 1 package finished [1.40s]
  build/trishul_navigation/pytest.xml: 3 tests, 0 errors, 0 failures, 1 skipped
  ```

To run tests locally:
```bash
source /opt/ros/jazzy/setup.bash
cd ~/trishul_ugv
colcon test --packages-select trishul_navigation
colcon test-result --all --verbose
```

---

## 9. Handoff & Git Information

* **Repository**: `https://github.com/Ethical-Coderss/trishul-ugv.git`
* **Branch**: `trishul-navigation`
* **Owner**: Navigation Lead
* **Pull Request**: [Open Pull Request](https://github.com/Ethical-Coderss/trishul-ugv/pull/new/trishul-navigation)
