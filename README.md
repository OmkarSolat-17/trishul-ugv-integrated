# Trishul UGV: Vision-Based Autonomous Navigation System

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6F00.svg)](https://gazebosim.org/docs/harmonic)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420.svg)](https://ubuntu.com/)
[![WSL](https://img.shields.io/badge/WSL_2-Windows_11-0078D6.svg)](https://learn.microsoft.com/en-us/windows/wsl/)
[![Build & Test](https://img.shields.io/badge/All_Subsystems-Operational_%26_Passing-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Problem Statement (BEL — ID 26126):** *Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment.*

---

## ⚡ Quickstart: Launch Complete System & Dashboard

Run the unified, single-command launcher (kills any lingering background processes, configures GPU acceleration, and boots all nodes):
```bash
cd /home/papa_ji/project/Trishul/merg-trishul
./run_demo.sh
```

You can select a simulation profile interactively from the terminal menu, or launch directly:
```bash
# 1) Standard UGV in Sandbox Proving Ground (AMCL Baseline):
./run_demo.sh --profile default

# 2) 4WD Skid-Steer UGV in City Normal World (SLAM Toolbox Online Mapping):
./run_demo.sh --profile city_normal_4wd

# 3) 4WD Skid-Steer UGV in Final City World (Complex Terrain, Flyovers, Bridges & Rivers):
./run_demo.sh --profile trishul_final_4wd
```

### Accessing the BVR Mission Control Web Dashboard:
* Open your browser at: **`http://127.0.0.1:8090`**
* **Tactical 2D SLAM Radar:** Click any point inside the arena to dispatch an autonomous Nav2 waypoint.
* **Dual-Camera Cockpit with PiP:** Switch between 3D Depth Thermal Heatmap, Tactical AI YOLO HUD, Forward Optical, and Rear Optical cameras.
* **10m Panoramic Area Scan:** Initiate a 360-degree sector sweep that dynamically explores and maps the environment.
* **Teleoperation & Safety:** Control the robot with on-screen D-Pad or keyboard **`[W/A/S/D]`**; adjust the dynamic speed slider; use the red **EMERGENCY STOP** button or **`[Spacebar]`** to instantly clamp velocities to zero.

---

## 🌟 System Architecture Overview

```
                    +-----------------------------------------------------+
                    |       Gazebo Harmonic Simulation (Physics & Worlds) |
                    |      - city_normal.sdf / trishul_final.sdf / models |
                    +--------------------------+--------------------------+
                                               | /scan, /camera/image_raw, /clock, /tf, /odom
                                               v
+---------------------------------------------------------------------------------------------------------+
|                                        TRISHUL ROS 2 ECOSYSTEM                                          |
|                                                                                                         |
|   +--------------------------+    +--------------------------+    +---------------------------------+   |
|   |   trishul_perception     |    |   trishul_localization   |    |       trishul_navigation        |   |
|   | - YOLO Object Detection  |    | - SLAM Toolbox 2D Online |    | - Nav2 Smac & NavFn Planners    |   |
|   | - 3D Metric Extraction   |    |   Async Mapping          |    | - DWB Dynamic Local Controller  |   |
|   | - Active Route Yielding  |    | - AMCL Particle Filter   |    | - 360 LiDAR Safety Brake        |   |
|   | - PointCloud2 Projection |    | - Sub-mm TF2 Broadcast   |    | - Custom Recovery Behaviors     |   |
|   +------------+-------------+    +------------+-------------+    +----------------+----------------+   |
|                |                               |                                   |                    |
+----------------|-------------------------------|-----------------------------------|--------------------+
                 | /ugv/combined/image           | TF (map -> base_footprint)        | /plan, Action      |
                 v                               v                                   v                    |
+---------------------------------------------------------------------------------------------------------+
|                               BACKEND: trishul_dashboard_server (Port 8090)                             |
|   - Multi-Threaded rclpy node + ThreadingHTTPServer serving REST API & MJPEG Streams                    |
|   - Nav2 Action Client (NavigateToPose) with distance and ETA calculation                               |
|   - Authoritative Latched Emergency Stop (E-STOP) hardware-level velocity clamp                         |
|   - Dynamic OccupancyGrid-to-RGBA base64 image converter (dilated crisp walls, transparent floors)      |
|   - 10m Panoramic Area Scan routine & Dynamic Speed Limit calibration REST endpoint                     |
+---------------------------------------------------------------------------------------------------------+
                                                 | REST API & Multi-Stream MJPEG Video
                                                 v
+---------------------------------------------------------------------------------------------------------+
|                           FRONTEND: BVR Tactical Ground Control Station (GCS)                           |
|   - Tactical HUD: Telemetry snapshot, battery monitoring, real-time FPS counter, YOLO decision badge    |
|   - Multi-Camera PiP Viewport: Optical RGB, RealSense 3D Depth Heatmap, Rear Camera, and AI YOLO HUD    |
|   - Interactive 2D SLAM Canvas: Interactive click-to-dispatch goal, laser points, dynamic robot reticle |
|   - Mission Execution: 10m Sector Scan, Sector Alpha/Bravo Patrols, Speed Slider, Keyboard Teleoperation|
+---------------------------------------------------------------------------------------------------------+
```

---

## 📦 Packages in this Repository

| Package | Purpose & Technologies | Documentation |
| :--- | :--- | :--- |
| **`trishul_bringup`** | Unified demo launch orchestrators (`demo.launch.py`, `city_4wd_demo.launch.py`), BVR Mission Control Web Dashboard server (Port 8090), and `./run_demo.sh` profile launcher. | [trishul_bringup/README.md](src/trishul_bringup/README.md) |
| **`trishul_navigation`** | Nav2 stack configuration (Smac/NavFn planners, DWB trajectory controller, custom recovery trees, 4WD profiles) and reactive LiDAR collision safety braking. | [trishul_navigation/README.md](src/trishul_navigation/README.md) |
| **`trishul_perception`** | Vision-AI engine: YOLO real-time object detection (`best.pt`), 3D metric extraction from RealSense depth, active route yielding/braking, and PointCloud2 costmap projection. | [trishul_perception/README.md](src/trishul_perception/README.md) |
| **`trishul_localization`** | State estimation: SLAM Toolbox online async mapping, AMCL particle filter localization, and sub-millimeter TF2 frame broadcasting. | [trishul_localization/README.md](src/trishul_localization/README.md) |
| **`trishul_simulation`** | Gazebo Harmonic physics environments, city worlds (`city_normal.sdf`, `trishul_final.sdf`), custom 3D models (bridges, flyovers, rivers), and `ros_gz_bridge`. | [trishul_simulation/README.md](src/trishul_simulation/README.md) |
| **`trishul_description`** | Complete 4WD Skid-Steer UGV model, URDF/Xacro kinematics, sensor placement (RGB-D camera, rear camera, 360 LiDAR, IMU) adhering to REP-103/REP-105 standards. | [trishul_description/README.md](src/trishul_description/README.md) |

---

## 💻 Hardware & Environment

- **Host Operating System**: Windows 11 (64-bit) with WSL 2 and WSLg hardware acceleration.
- **Guest Operating System**: Ubuntu 24.04 LTS (Noble Numbat).
- **GPU Acceleration**: NVIDIA GeForce RTX via Direct3D 12 Gallium driver (`GALLIUM_DRIVER=d3d12`, `MESA_D3D12_DEFAULT_ADAPTER_NAME="NVIDIA"`).
- **Robotics Middleware**: ROS 2 Jazzy Jalisco.
- **Physics Simulation**: Gazebo Harmonic (`ros_gz`).
- **Python / AI**: Python 3.12, PyTorch / YOLOv8, OpenCV 4.8+.

---

## 📋 Comprehensive Documentation Index

- [Master System Documentation](docs/SYSTEM_DOCUMENTATION.md) — Comprehensive technical manual and architectural breakdown.
- [Mission Control Web Dashboard Guide](docs/MISSION_CONTROL_DASHBOARD.md) — Tactical GCS user manual, API endpoints, and features.
- [Architecture Overview](docs/ARCHITECTURE_OVERVIEW.md) — Detailed block diagrams and subsystem interaction contracts.
- [Environment Setup Guide](docs/ENVIRONMENT_SETUP_GUIDE.md) — Complete setup instructions for WSL 2, ROS 2 Jazzy, and Gazebo Harmonic.
- [Contributing & Git Workflow](CONTRIBUTING.md) — Team standards, code quality checks, and commit guidelines.

---

## 🛡️ License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.
