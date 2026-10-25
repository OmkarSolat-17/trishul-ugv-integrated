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
|   | - 3D Spatial Metrics (Z) |    | - SLAM Toolbox 2D Online |    | - Sensor Monitor Reactive Emergency Brake  |   |
|   | - Active Route Yielding  |    | - AMCL Particle Filter   |    | - PointCloud2 Vision Costmap Obstacle Feed |   |
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
|   - Multi-feed streaming: Depth Heatmap, YOLO HUD, Forward Optical, Rear Camera, and 10m Panoramic Sweep.         |
+--------------------------------------------------------------------------------------------------------------------+
                                                 | REST API, Telemetry JSON, MJPEG Video Streams
                                                 v
+--------------------------------------------------------------------------------------------------------------------+
|                                FRONTEND: BVR Tactical Mission Control Web Dashboard                                |
|   - Tactical HUD: System status, latched E-STOP, live battery telemetry, real-time FPS counter.                     |
|   - Dual-Vision Cockpit: Multi-stream selector with Picture-in-Picture (PiP) swapping.                             |
|   - Interactive 2D SLAM Radar: True map rendering, 360 LiDAR point projection, interactive click-to-nav goal.      |
|   - Teleoperation: D-Pad controls, dynamic speed limit slider (0.05 - 2.50 m/s), keyboard driving [W/A/S/D/Space]. |
|   - Tactical Event Terminal: Real-time mission logging, coordinate feedback, boundary snapping, and audit trail.   |
+--------------------------------------------------------------------------------------------------------------------+
```

---

## 2. Beyond Visual Range (BVR) Ground Control Station

### What is BVR in the Trishul Platform?
In defense and field robotics, **Beyond Visual Range (BVR)** (or Beyond Visual Line of Sight - BVLOS) denotes operating the vehicle when the operator has no direct line-of-sight to the platform. 

The Trishul BVR Mission Control Dashboard bridges this operational gap by synthesizing:
1. **Authoritative 2D SLAM Situational Awareness**: The operator views an exact, real-time metric occupancy grid of the arena, dynamically updated with 360° LiDAR points and the vehicle's true position.
2. **Multi-Camera & 3D Thermal Vision**: The operator can switch between optical stereo cameras, physical rear cameras, and 3D depth thermal heatmaps to verify traversability even in low-light or degraded visual conditions.
3. **AI Tactical Decision Feedback**: Visual hazards detected by YOLO (vehicles, barricades, humans) are highlighted with metric distance and lateral offset, informing the operator of automated yield or brake events.
4. **Instant Emergency Intervention**: Latched E-STOP and manual keyboard override allow instant remote operator intervention at any moment.

---

## 3. Frozen ROS 2 Interface Contracts & Coordinate Frames

The Trishul software stack strictly conforms to standard ROS 2 conventions (REP-103: Standard Units of Measure, REP-105: Coordinate Frames):

### Coordinate Frame Hierarchy (TF2 Tree)
```
  map (Global SLAM / AMCL frame)
   └── odom (Continuous wheel odometry frame, drift-accumulating)
        └── base_footprint (2D projection on ground surface)
             └── base_link (Robot center of geometry and mass)
                  ├── base_scan (360 LiDAR scanner frame)
                  ├── camera_link -> camera_optical_frame (Forward RGB-D)
                  ├── rear_camera_link (Rear optical camera)
                  └── wheel_*_link (Four-wheel drive kinematics)
```

### Active ROS 2 Topics

| Topic | Type | Frame | Purpose |
| :--- | :--- | :--- | :--- |
| `/scan` | `sensor_msgs/msg/LaserScan` | `base_scan` | 360° 2D LiDAR range measurements (0.20m to 12.0m). |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | `camera_optical_frame` | Raw forward camera optical sensor stream. |
| `/ugv/combined/image` | `sensor_msgs/msg/Image` | `camera_optical_frame` | 3D depth perception heatmap with Turbo colormap and HUD. |
| `/ugv/yolo/image` | `sensor_msgs/msg/Image` | `camera_optical_frame` | Tactical HUD video with YOLO detection bounding boxes. |
| `/ugv/rear_camera/image`| `sensor_msgs/msg/Image` | `rear_camera_link` | Physical rear camera optical feed. |
| `/ugv/perception/obstacles_pc` | `sensor_msgs/msg/PointCloud2` | `camera_optical_frame` | 3D obstacle projection into Nav2 costmaps. |
| `/odom` | `nav_msgs/msg/Odometry` | `odom -> base_footprint` | High-frequency (30 Hz) differential/skid-steer wheel odometry. |
| `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | Dynamic | Complete system kinematic transform tree. |
| `/map` | `nav_msgs/msg/OccupancyGrid` | `map` | Global static/SLAM 2D grid map with resolution and origin metadata. |
| `/cmd_vel` | `geometry_msgs/msg/Twist` | N/A | Velocity command input consumed by motor controller. |
| `/plan` | `nav_msgs/msg/Path` | `map` | Global obstacle-free trajectory path generated by Nav2. |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | `map` | Goal dispatch and progress feedback action server. |

---

## 4. Verification & Demonstration Commands

To launch the complete system cleanly with one command:
```bash
./run_demo.sh
```

On WSL2 machines without hardware OpenGL 3.3+ acceleration, `./run_demo.sh` automatically switches Gazebo Harmonic to server-only mode (`-s`) under `xvfb-run` + Mesa `llvmpipe` software rendering (or force it explicitly via `./run_demo.sh --headless --profile city_normal_4wd`).

Supported simulation profiles:
- **`--profile default`**: Standard UGV in TB3 Sandbox with AMCL & 2D LiDAR.
- **`--profile city_normal_4wd`**: 4WD Skid-Steer UGV in City Normal World with SLAM Toolbox.
- **`--profile trishul_final_4wd`**: 4WD Skid-Steer UGV in Final City World with SLAM Toolbox and complex terrain.

To access the Mission Control Dashboard:
* Open Google Chrome, Brave, or Edge at: **`http://127.0.0.1:8090`**
* Verify telemetry header: `SYS: OPERATIONAL / STANDBY`, `BATTERY: 98% [26.4V]`.
* Test live slider: Drag speed limit slider to calibrate vehicle cruising velocity.
* Test click-to-navigate: Click any point inside the tactical map to dispatch an autonomous goal.
