# Trishul UGV: Vision-Based Autonomous Navigation System

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6F00.svg)](https://gazebosim.org/docs/harmonic)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420.svg)](https://ubuntu.com/)
[![WSL](https://img.shields.io/badge/WSL_2-Windows_11-0078D6.svg)](https://learn.microsoft.com/en-us/windows/wsl/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Problem Statement**: *Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment.*

---

## 1. Project Overview

**Trishul** is a simulation-based autonomous unmanned ground vehicle (UGV) navigation prototype engineered for rugged outdoor environments. The project is designed to progressively demonstrate:

1. **Realistic Outdoor Simulation**: A simulated UGV operating in an outdoor Gazebo environment with realistic physics, terrain variations, and lighting.
2. **Sensor Suite Simulation**: Onboard cameras (monocular / stereo / RGB-D) and complementary proprioceptive sensors (IMU, wheel encoders).
3. **Vision & AI Perception**: Monocular/RGB camera processing, AI-driven hazard and obstacle detection, and traversability estimation.
4. **Mapping & Localization**: Robust state estimation and spatial mapping, targeting **visual SLAM / visual odometry** as a primary localization source.
5. **Autonomous Navigation**: Waypoint-based Point A to Point B goal navigation using the ROS 2 Navigation stack (Nav2).
6. **Dynamic Obstacle Avoidance**: Real-time costmap updates from visual perception with local replanning and obstacle avoidance.
7. **Comprehensive Visualization**: Live telemetry, sensor feeds, point clouds, costmaps, and vehicle trajectories displayed in RViz 2 and Gazebo.
8. **Reproducible Demonstration**: Complete end-to-end execution guaranteed on a single Windows 11 host laptop running WSL 2 (Ubuntu 24.04 LTS).

---

## 2. Current Project Status

> ⚠️ **STATUS: REPOSITORY SKELETON INITIALIZED (PRE-IMPLEMENTATION)**
>
> All ROS 2 packages and algorithm implementations are currently in **skeleton / placeholder** phase.
> - The robot model (URDF/Xacro), simulation world, AI perception models, SLAM pipelines, and Nav2 controllers are **NOT yet implemented**.
> - Empty package directories are preserved via `.gitkeep` and will be properly initialized using `ros2 pkg create` as development starts.

---

## 3. Technology Stack & Target Baseline

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Host System** | Windows 11 (64-bit) | WSLg enabled for native hardware-accelerated GUI output |
| **Guest OS** | Ubuntu 24.04 LTS (Noble Numbat) | WSL 2 virtualized Linux kernel |
| **Robotics Middleware**| ROS 2 Jazzy Jalisco | Primary Tier-1 LTS release for Ubuntu 24.04 |
| **Physics Simulation** | Gazebo Harmonic (`ros_gz`) | Official modern simulation suite paired with ROS 2 Jazzy |
| **Navigation** | Nav2 (Navigation 2) | Official ROS 2 Jazzy Nav2 stack |
| **Visualization** | RViz 2 & Gazebo Sim GUI | Hardware-accelerated via DirectX/Mesa inside WSLg |

For complete environment verification and installation instructions, see [docs/ENVIRONMENT_SETUP_GUIDE.md](docs/ENVIRONMENT_SETUP_GUIDE.md).

---

## 4. Repository Structure

```text
trishul-ugv/
├── README.md               # Project overview, system status, and getting started
├── .gitignore              # Ignores ROS 2 build artifacts, logs, models, and environments
├── CONTRIBUTING.md         # Git branching, commit standards, reviews, and package rules
├── LICENSE                 # Apache 2.0 Open Source License
├── docs/                   # Architectural guides, interface checklists, and setup manuals
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── ENVIRONMENT_SETUP_GUIDE.md
│   └── INTERFACE_PLANNING_CHECKLIST.md
├── src/                    # ROS 2 colcon workspace source directory
│   ├── trishul_description/ # UGV URDF/Xacro, kinematics, meshes, and physical parameters
│   ├── trishul_simulation/  # Gazebo Harmonic worlds, launch configs, and ros_gz bridge
│   ├── trishul_perception/  # Camera processing, AI object/hazard detection, traversability
│   ├── trishul_localization/# Sensor fusion, visual SLAM investigation, odometry
│   ├── trishul_navigation/  # Nav2 costmaps, path planners, trajectory controllers
│   └── trishul_bringup/     # System-wide launch files, RViz configs, master integration
├── tests/                  # Integration tests, system verification scripts
├── scripts/                # Utility scripts for workspace setup, asset downloads
├── results/                # Demonstration logs, benchmarks, and evaluation outputs
└── requirements/           # Python and system dependency declarations
```

---

## 5. Team Roles & Ownership

| Role | Lead | Primary Scope | Directory Responsibility |
| :--- | :--- | :--- | :--- |
| **1. Simulation Lead** | Simulation Lead | Robot description, simulation worlds, sensors | `src/trishul_description/`<br>`src/trishul_simulation/` |
| **2. Vision / AI Lead** | Vision/AI Lead | Camera pipeline, AI detection, traversability | `src/trishul_perception/`<br>`requirements/` |
| **3. Localization Lead**| Localization Lead | Visual SLAM, odometry fusion, coordinate frames | `src/trishul_localization/` |
| **4. Navigation Lead**  | Navigation Lead | Nav2 configuration, path planning, obstacle avoidance | `src/trishul_navigation/` |
| **5. Integration Lead** | Integration Lead | System bringup, launch orchestration, tests, Git workflow | `src/trishul_bringup/`<br>`docs/`, `scripts/`, `tests/` |

---

## 6. Interface Planning

Before implementing custom messages or hardcoding topic names, all leads must consult and fill out the [Interface Planning Checklist](docs/INTERFACE_PLANNING_CHECKLIST.md). Standard coordinate conventions (REP-103) and frame trees (REP-105: `map` -> `odom` -> `base_link`) must be followed strictly.

---

## 7. Next Steps & Development Roadmap

1. **Step 1 (Environment)**: Ensure all team members have completed [docs/ENVIRONMENT_SETUP_GUIDE.md](docs/ENVIRONMENT_SETUP_GUIDE.md) in WSL 2.
2. **Step 2 (Interface Sign-off)**: Complete the [Interface Planning Checklist](docs/INTERFACE_PLANNING_CHECKLIST.md) during the initial architectural meeting.
3. **Step 3 (Package Initialization)**: Initialize packages using `ros2 pkg create` inside `src/`.
4. **Step 4 (Phase 1 Milestone)**:
   - Simulation lead brings up a minimal mobile base in Gazebo Harmonic with camera sensor.
   - Integration lead creates `trishul_bringup` to visualize the robot and camera feed in RViz 2.
