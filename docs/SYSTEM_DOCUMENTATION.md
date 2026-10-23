# Trishul UGV: Master System Documentation & Technical Manual

> **Problem Statement (BEL — ID 26126):** *Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment.*  
> **Platform:** ROS 2 Jazzy Jalisco | Gazebo Harmonic | Ubuntu 24.04 LTS (WSL2 / Native)  
> **Deliverable:** Fully integrated autonomous UGV software stack with Beyond Visual Range (BVR) Tactical Ground Control Station (GCS).

---

## 1. System Architecture Overview

Trishul is an autonomous Unmanned Ground Vehicle (UGV) navigation and mission control platform. It integrates sensory perception, SLAM-based self-localization, autonomous path planning, reactive obstacle collision avoidance, and a real-time web-based Beyond Visual Range (BVR) Ground Control Station.

```
                                      +---------------------------------------------+
                                      |         Gazebo Harmonic Simulation          |
                                      |     (or Physical UGV Hardware Platform)     |
                                      +----------------------+----------------------+
                                                             | /camera/image_raw, /scan,
                                                             | /odom, /tf, /clock
                                                             v
+--------------------------------------------------------------------------------------------------------------------+
|                                              TRISHUL ROS 2 ECOSYSTEM                                               |
|                                                                                                                    |
|   +--------------------------+    +--------------------------+    +--------------------------------------------+   |
|   |   trishul_perception     |    |   trishul_localization   |    |             trishul_navigation             |   |
|   | - 3D Depth Thermal Map   |    | - TF2 Map-to-Footprint   |    | - Nav2 Smac & NavFn Global Path Planners   |   |
|   | - YOLO Object Detections |    |   Transform Broadcaster  |    | - DWB Dynamic Local Trajectory Controller  |   |
|   | - MJPEG Stream Pipeline  |    | - AMCL / SLAM Toolbox    |    | - Sensor Monitor Reactive Emergency Brake  |   |
|   +------------+-------------+    +------------+-------------+    +---------------------+----------------------+   |
|                |                               |                                        |                          |
+----------------|-------------------------------|----------------------------------------|--------------------------+
                 | /ugv/combined/image           | TF (map -> base_footprint)             | /plan, Action Status     |
                 v                               v                                        v                          |
+--------------------------------------------------------------------------------------------------------------------+
|                                    BACKEND: trishul_dashboard_server (Port 8090)                                   |
|   - Multi-Threaded rclpy node running concurrently with Python ThreadingHTTPServer on 127.0.0.1:8090.              |
|   - Real-time TF2 transform resolver ensuring 100% synchronization with RViz and global map coordinates.           |
|   - Nav2 Action Client (NavigateToPose) with distance remaining and ETA calculation.                               |
|   - Latched authoritative Emergency Stop (E-STOP) hardware-level velocity clamp.                                    |
|   - Dynamic OccupancyGrid-to-RGBA base64 image converter (dilated crisp walls, transparent floors).                |
+--------------------------------------------------------------------------------------------------------------------+
                                                 | REST API, Telemetry JSON, MJPEG Video Stream
                                                 v
+--------------------------------------------------------------------------------------------------------------------+
|                                FRONTEND: BVR Tactical Mission Control Web Dashboard                                |
|   - Tactical HUD: System status, latched E-STOP, live battery telemetry, real-time FPS counter.                     |
|   - 3D Depth Vision: Thermal colormap (Turbo) stream with live frame-rate and sensor health status.                |
|   - Interactive 2D SLAM Scanner: True map rendering, 360 LiDAR point projection, interactive click-to-nav goal.   |
|   - Teleoperation: D-Pad controls, dynamic speed limit slider (0.05 - 0.50 m/s), keyboard driving [W/A/S/D/Space].|
|   - Tactical Event Terminal: Real-time mission logging, coordinate feedback, boundary snapping, and audit trail.   |
+--------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Beyond Visual Range (BVR) Ground Control Station

### What is BVR in the Trishul Platform?
In defense and field robotics, **Beyond Visual Range (BVR)** (or Beyond Visual Line of Sight - BVLOS) denotes operating the vehicle when the operator has no direct line-of-sight to the platform. 

The Trishul Mission Control Web Dashboard functions as the primary BVR Ground Control Station (GCS). It bridges all physical and simulated onboard sensors over standard TCP/IP networking, enabling full remote command, observation, and intervention:
1. **Visual Situational Awareness:** Operators observe terrain geometry via the forward-facing 3D depth perception stream and object detection bounding boxes.
2. **Tactical Geospatial Awareness:** The 360 LiDAR radar scanner and SLAM map show obstacles, walls, pillars, and unexplored sectors up to 12 meters ahead.
3. **Telepresence Control:** Operators can either dispatch autonomous waypoints via interactive map clicks or take direct manual control using the low-latency teleoperation D-pad and adjustable speed governor.
4. **Authoritative Safety:** A single-click Emergency Stop halts all motor power within 20 milliseconds, overriding autonomous planners and manual inputs.

---

## 3. Python Server REST & Streaming API Specification

The dashboard server (`dashboard_server.py`) exposes a robust HTTP REST and streaming interface on `http://127.0.0.1:8090`:

### Endpoints Summary

| Endpoint | Method | Input Format | Output Format | Purpose & Behavior |
| :--- | :---: | :--- | :--- | :--- |
| **`/`** | `GET` | None | `text/html` | Serves the main tactical mission control web client (`index.html`). |
| **`/api/state`** | `GET` | None | `application/json` | Returns comprehensive real-time telemetry snapshot (pose, velocities, battery, LiDAR points, planned path, detections, map metadata). |
| **`/stream/video`** | `GET` | None | `multipart/x-mixed-replace` | Live MJPEG video stream from `/ugv/combined/image` (with auto-fallback to raw `/camera/image_raw`). |
| **`/api/goal`** | `POST` | `application/json` | `application/json` | Dispatches an autonomous `NavigateToPose` action goal to Nav2. |
| **`/api/cancel`** | `POST` | None | `application/json` | Preempts and cancels the active Nav2 navigation goal, resetting the robot to `IDLE`. |
| **`/api/teleop`** | `POST` | `application/json` | `application/json` | Sends direct velocity commands to `/cmd_vel` (honors speed limit slider and latched E-STOP). |
| **`/api/estop`** | `POST` | None | `application/json` | Engages the latched Authoritative Emergency Stop; immediately zeroes velocity and cancels active Nav2 goals. |
| **`/api/reset_estop`**| `POST` | None | `application/json` | Clears the E-STOP latch and restores motor drive authorization. |

---

## 4. Frozen ROS 2 Interface Contracts & Coordinate Frames

The Trishul software stack strictly conforms to standard ROS 2 conventions (REP-103: Standard Units of Measure, REP-105: Coordinate Frames):

### Coordinate Frame Hierarchy (TF2 Tree)
```
  map (Global SLAM / AMCL frame)
   └── odom (Continuous wheel odometry frame, drift-accumulating)
        └── base_footprint (2D projection on ground surface)
             └── base_link (Robot center of geometry and mass)
                  ├── base_scan (360 LiDAR scanner frame)
                  ├── wheel_left_link / wheel_right_link
                  └── camera_link (Forward perception optical frame)
```

### Active ROS 2 Topics

| Topic | Type | Frame | Purpose |
| :--- | :--- | :--- | :--- |
| `/scan` | `sensor_msgs/msg/LaserScan` | `base_scan` | 360 2D LiDAR range measurements (0.20m to 12.0m). |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | `camera_optical_frame`| Raw forward camera sensor stream. |
| `/ugv/combined/image` | `sensor_msgs/msg/Image` | `camera_optical_frame`| 3D depth perception heatmap with Turbo colormap and HUD telemetry. |
| `/odom` | `nav_msgs/msg/Odometry` | `odom -> base_footprint` | High-frequency (30 Hz) differential drive wheel odometry. |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | Dynamic | Complete system kinematic transform tree. |
| `/map` | `nav_msgs/msg/OccupancyGrid` | `map` | Global static/SLAM 2D grid map with resolution and origin metadata. |
| `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | `map` | Probabilistic localization estimate from AMCL particle filter. |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | N/A | Velocity command input consumed by differential drive motor controller. |
| `/plan` | `nav_msgs/msg/Path` | `map` | Global obstacle-free trajectory path generated by Nav2. |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | `map` | Goal dispatch and progress feedback action server. |

---

## 5. Technical Architecture & Strategic Roadmap

### Q1: Where is SLAM in our dashboard?
**Answer:** SLAM is the foundation of the right-hand panel (**`[TACTICAL 2D MAP & 360 LIDAR SCANNER]`**):
* When launched with `slam:=True`, `slam_toolbox` generates the live occupancy grid on `/map`.
* The dashboard displays this grid in real time: dark slate denotes free space, electric cyan denotes walls/obstacles, and amber indicates inflation proximity layers.
* Overlaid on the SLAM map are the robot's authoritative pose (resolved from TF2 `map -> base_footprint`) and live LiDAR points.

### Q2: How can we view the Camera Feed and Depth Heatmap together?
**Answer:** In the future revision, the left visual panel can be configured in one of three ways:
1. **Split-Screen Dual Stream:** A side-by-side 2x1 grid displaying RGB Optical Camera (left) and 3D Depth Heatmap (right).
2. **Picture-in-Picture (PiP):** Full-screen RGB video with a high-contrast depth heatmap inset thumbnail in the bottom-right corner.
3. **Fused Alpha HUD:** Direct OpenCV pixel blending where depth gradients are overlaid semi-transparently on top of optical camera frames.

### Q3: Why is LiDAR used as the primary navigation sensor instead of Camera alone?
**Answer:** In outdoor defense environments (BEL Problem Statement ID 26126):
* **Lighting Immunity:** Cameras fail or degrade under direct sunlight glare, heavy shadows, dust, and complete nighttime darkness. LiDAR emits its own light (active infrared laser) and functions 24/7.
* **Direct Distance Measurement:** LiDAR provides exact distance in millimeters without algorithmic latency. Standard 2D cameras require heavy stereo matching or neural network depth estimation.
* **Optimal Sensor Fusion:** The Trishul architecture uses **LiDAR for uncompromised safety and path planning**, and the **Camera for semantic intelligence** (recognizing obstacles, humans, vehicles, and road boundaries).

---

## 6. Verification & Demonstration Commands

To launch the complete system cleanly with one command:
```bash
cd /home/papa_ji/project/Trishul/merg-trishul
./run_demo.sh
```

To access the Mission Control Dashboard:
* Open Google Chrome, Brave, or Edge at: **`http://127.0.0.1:8090`**
* Verify telemetry header: `SYS: OPERATIONAL / STANDBY`, `BATTERY: 98% [26.4V]`.
* Test live slider: Drag speed limit slider to verify immediate text and motor limit scaling.
* Test click-to-navigate: Click any point inside the tactical map to dispatch an autonomous goal.
