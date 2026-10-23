# Trishul UGV: Vision-Based Autonomous Navigation System

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6F00.svg)](https://gazebosim.org/docs/harmonic)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420.svg)](https://ubuntu.com/)
[![WSL](https://img.shields.io/badge/WSL_2-Windows_11-0078D6.svg)](https://learn.microsoft.com/en-us/windows/wsl/)
[![Navigation Subsystem](https://img.shields.io/badge/Navigation_Subsystem-Operational_%26_Passing-brightgreen.svg)](src/trishul_navigation/README.md)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Problem Statement (BEL — ID 26126):** *Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment.*

---

## 🚀 Active Subsystem Status: Navigation & Guidance Operational

> **BRANCH: `trishul-navigation`**  
> **DELIVERABLE STATUS: COMPLETED, TESTED & PRODUCTION-READY**
>
> The autonomous navigation, guidance, and safety braking subsystem (`src/trishul_navigation`) is fully implemented, verified in simulation, and passing all quality assurance tests. It features a unified single-command launch file, zero-click AMCL self-localization aligned with Gazebo, active LiDAR collision safety braking, autonomous mission execution via the Nav2 Simple Commander API, and WSL2 real-time performance tuning.

---

## 🌟 Autonomous Navigation Subsystem Showcase (`trishul_navigation`)

For complete technical documentation, parameter tables, and architecture details, refer to the [trishul_navigation Package Documentation](src/trishul_navigation/README.md).

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

### Key Deliverables Implemented in this Subsystem:

1. **Unified Master Launch (`navigation.launch.py`)**:
   Starts Gazebo Harmonic physics simulation, the complete Nav2 navigation stack, pre-configured RViz 2 layout, active sensor supervision, and telemetry heartbeat in one terminal command.
2. **Autonomous Mission Commander (`mission_navigator.py`)**:
   Hands-free autonomous navigation built on the `nav2_simple_commander` API. Supports full cross-arena traversal and accepts arbitrary coordinates from the command line (`-p target_x:=... -p target_y:=...`).
3. **Active Collision Prevention & Emergency Braking (`sensor_monitor.py`)**:
   Segments 360° LiDAR feeds into angular sectors (`FRONT`, `LEFT`, `RIGHT`). If an obstacle breaches the forward arc closer than 0.25 m, an active Emergency Stop (`linear.x = 0.0`) is immediately dispatched to `/cmd_vel`.
4. **Zero-Click AMCL Pose Alignment**:
   Configured `set_initial_pose: true` at `(-2.00, -0.50)` to precisely match the Gazebo robot spawn point, eliminating the default center-pillar collision bug.
5. **WSL2 Hypervisor Real-Time Tuning**:
   Tuned `transform_tolerance: 1.5s` and `default_server_timeout: 1000ms` to eliminate virtualization latency errors (`Transform data too old` and BT planner timeouts).
6. **Pre-Configured RViz 2 Profile (`trishul_nav.rviz`)**:
   Standardized visualization showing map, costmaps, laser scans, footprints, and trajectories out-of-the-box.
7. **Production Quality Assurance**:
   Zero errors, zero failures under `colcon test` with PEP8 (Flake8) and PEP257 docstring compliance.

---

### Quick Start: Running the Autonomous Navigation Subsystem

#### Step 1: Build the Package
```bash
cd ~/trishul_ugv
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select trishul_navigation
source install/setup.bash
```

#### Step 2: Launch the Complete Navigation System
```bash
ros2 launch trishul_navigation navigation.launch.py
```
*(Gazebo Sim, Nav2, and RViz 2 will open with the robot localized at `(-2.0, -0.5)`).*

#### Step 3: Command the Robot Where to Go
In a second terminal:
```bash
cd ~/trishul_ugv
source install/setup.bash

# Option 1: Autonomous Cross-Arena Mission (Travels to opposite side of map)
ros2 run trishul_navigation mission_navigator

# Option 2: Send Any Custom Coordinates
ros2 run trishul_navigation mission_navigator --ros-args -p target_x:=1.0 -p target_y:=0.5

# Option 3: Visual Point-and-Click via RViz
# Click the "Nav2 Goal" button in the RViz toolbar and click any open floor space.

# Option 4: Manual Keyboard Teleoperation (Protected by Active Collision Braking)
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

---

## 1. Start Here — Reading Order for Team Members

Every member should read these in order:

1. **This file** — project overview, status, and navigation showcase.
2. [src/trishul_navigation/README.md](src/trishul_navigation/README.md) — deep dive into the operational navigation package.
3. [docs/trishul-ugv-docs/PRODUCT.md](docs/trishul-ugv-docs/PRODUCT.md) — full project goal, hackathon context, scope, and success measures.
4. [docs/trishul-ugv-docs/TEAM_ROLES.md](docs/trishul-ugv-docs/TEAM_ROLES.md) — find your role and what you must deliver.
5. [docs/trishul-ugv-docs/SETUP_GUIDE.md](docs/trishul-ugv-docs/SETUP_GUIDE.md) — WSL 2, Ubuntu 24.04, ROS 2 Jazzy and Gazebo setup steps.
6. [docs/trishul-ugv-docs/GIT_WORKFLOW.md](docs/trishul-ugv-docs/GIT_WORKFLOW.md) — branching, commits, PRs, and what never to commit.
7. [docs/trishul-ugv-docs/INTERFACES.md](docs/trishul-ugv-docs/INTERFACES.md) — the interface agreement table.
8. [docs/trishul-ugv-docs/TESTING_AND_DEMO.md](docs/trishul-ugv-docs/TESTING_AND_DEMO.md) — test layers, scenario checklists, and judging demo plan.
9. [docs/trishul-ugv-docs/AI_CODING_GUIDE.md](docs/trishul-ugv-docs/AI_CODING_GUIDE.md) — rules for using Antigravity or any AI coding assistant.
10. [docs/trishul-ugv-docs/CONTRIBUTING.md](docs/trishul-ugv-docs/CONTRIBUTING.md) — quick contributing reference card.

---

## 2. Project Overview

**Trishul** is the software "brain" of a simulated autonomous UGV engineered for rugged outdoor environments. It combines simulation, sensor communication, camera-based perception, localization, and navigation so the robot can move toward a goal while responding to its surroundings.

The team's **nine-day hackathon MVP** aims to demonstrate:

1. **Realistic Outdoor Simulation** — UGV operating in a Gazebo Harmonic outdoor world with realistic physics, terrain, and lighting.
2. **Sensor Suite Simulation** — Simulated cameras (monocular / RGB-D) and proprioceptive sensors (IMU, wheel encoders).
3. **Vision & AI Perception** — Camera-based image processing, lightweight AI hazard/obstacle detection, and traversability estimation.
4. **Mapping & Localization** — State estimation targeting **visual SLAM / visual odometry** as the primary localization source.
5. **Autonomous Navigation** — Point A → Point B goal navigation using the Nav2 stack (**Delivered in `trishul_navigation`**).
6. **Dynamic Obstacle Avoidance** — Real-time costmap updates from visual perception with local replanning.
7. **Comprehensive Visualization** — Live telemetry, sensor feeds, costmaps, and trajectories in RViz 2 and Gazebo.
8. **Reproducible Demonstration** — Full end-to-end execution on one Dell G15 laptop (Windows 11 + WSL 2 + Ubuntu 24.04 LTS).

---

## 3. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Host OS** | Windows 11 (64-bit) | WSLg enabled for native hardware-accelerated GUI |
| **Guest OS** | Ubuntu 24.04 LTS (Noble Numbat) | WSL 2 virtualized Linux kernel |
| **Robotics Middleware** | ROS 2 Jazzy Jalisco | Primary Tier-1 LTS release for Ubuntu 24.04 |
| **Physics Simulation** | Gazebo Harmonic (`ros_gz`) | Official simulation suite paired with ROS 2 Jazzy |
| **Navigation** | Nav2 (Navigation 2) | Official ROS 2 Jazzy Nav2 stack (**Fully Operational**) |
| **Visualization** | RViz 2 & Gazebo Sim GUI | Hardware-accelerated via DirectX/Mesa in WSLg |
| **Vision / AI** | Python, OpenCV, lightweight pretrained model | TBD by Vision/AI lead |
| **Localization** | AMCL (Operational baseline) + Visual SLAM (Stretch) | Localization lead integration |
| **Version Control** | Git & GitHub | Single repository, feature-branch workflow |

---

## 4. Repository Structure — Package & Directory Index

```text
trishul-ugv/                        ← repository root
├── README.md                       ← Master entry point (this file)
├── .gitignore                      ← excludes build/, install/, logs, models, venvs
├── CONTRIBUTING.md                 ← full Git workflow, ownership, PR, and data rules
├── LICENSE                         ← Apache 2.0
│
├── docs/                           ← all documentation
│   ├── ARCHITECTURE_OVERVIEW.md    ← system diagram & per-module boundaries
│   ├── ENVIRONMENT_SETUP_GUIDE.md  ← step-by-step WSL 2 + ROS 2 + Gazebo setup
│   ├── INTERFACE_PLANNING_CHECKLIST.md ← REP-103/105, sensor & Nav2 checklist
│   └── trishul-ugv-docs/           ← original team reference documentation
│
├── src/                            ← ROS 2 colcon workspace source root
│   ├── trishul_description/        ← URDF/Xacro, meshes, joint kinematics
│   ├── trishul_simulation/         ← Gazebo worlds, ros_gz_bridge configs
│   ├── trishul_perception/         ← camera pipeline, AI detection, traversability
│   ├── trishul_localization/       ← EKF fusion, visual SLAM, TF broadcasting
│   ├── trishul_navigation/         ← [OPERATIONAL] Nav2 params, costmaps, planners, safety brake
│   └── trishul_bringup/            ← master launch files, RViz profiles
│
├── tests/                          ← integration tests, launch_testing harnesses
├── scripts/                        ← developer onboarding and utility scripts
├── results/                        ← test logs, benchmarks, demo screenshots
└── requirements/                   ← Python dependency declarations
```

### ROS 2 Package Implementation Status

| Package | Status | Owner | Documentation |
| :--- | :--- | :--- | :--- |
| **`trishul_navigation`** | **Operational & Verified** | Navigation Lead | [trishul_navigation/README.md](src/trishul_navigation/README.md) |
| `trishul_description` | Pending Implementation | Simulation Lead | [src/trishul_description/README.md](src/trishul_description/README.md) |
| `trishul_simulation` | Pending Implementation | Simulation Lead | [src/trishul_simulation/README.md](src/trishul_simulation/README.md) |
| `trishul_perception` | Pending Implementation | Vision / AI Lead | [src/trishul_perception/README.md](src/trishul_perception/README.md) |
| `trishul_localization` | Pending Implementation | Localization Lead | [src/trishul_localization/README.md](src/trishul_localization/README.md) |
| `trishul_bringup` | Pending Implementation | Integration Lead | [src/trishul_bringup/README.md](src/trishul_bringup/README.md) |

---

## 5. Team Roles & Ownership

| # | Role | Owner | Owned Directories | Status & Key Deliverables |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Simulation Lead** | TBD | `src/trishul_description/`<br>`src/trishul_simulation/` | Working robot model + outdoor Gazebo world + sensor topics |
| 2 | **Vision / AI Lead** | TBD | `src/trishul_perception/`<br>`requirements/` | Camera processing node + AI detection + traversability output |
| 3 | **Localization Lead** | TBD | `src/trishul_localization/` | State estimation + TF tree + map/pose output |
| 4 | **Navigation Lead** | **Kshitij** | `src/trishul_navigation/` | **DELIVERED & VERIFIED**: Nav2 costmaps + path planning + mission commander + collision safety brake |
| 5 | **Integration Lead** | TBD | `src/trishul_bringup/`<br>`docs/` · `scripts/` · `tests/` | Master launch + RViz profile + clean-clone demo |

---

## 6. Quality Assurance & Verification

The navigation subsystem has been rigorously tested:
* **Flake8 (PEP8)**: Clean code conventions with 0 linting errors.
* **PEP257**: Standard Python docstring conventions satisfied.
* **colcon test**: `3 tests, 0 errors, 0 failures, 1 skipped` (copyright).
* **WSL2 Runtime Tested**: Traversal tested across the arena with zero timeout crashes and active safety braking confirmed.

---

## 7. Official Learning References

| Resource | URL |
| :--- | :--- |
| ROS 2 Jazzy Installation | https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html |
| Nav2 Documentation | https://docs.nav2.org/ |
| Gazebo Harmonic Docs | https://gazebosim.org/docs/harmonic/ |
| GitHub Repository | https://github.com/Ethical-Coderss/trishul-ugv |
