# trishul_bringup: Master System Integration & BVR Ground Control Station

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)
[![Status](https://img.shields.io/badge/Status-Operational_%26_Passing-brightgreen.svg)]()

The **`trishul_bringup`** package is the central deployment and operational orchestrator of the Trishul UGV platform. It integrates physics simulation, autonomous navigation, visual perception, and state estimation into unified launch pipelines, and hosts the **Beyond Visual Range (BVR) Tactical Ground Control Station (GCS)** web dashboard.

---

## 🚀 Key Deliverables & Components

### 1. Unified Launch Orchestrators
- **`demo.launch.py`**:
  Default end-to-end mission launch file. Starts Gazebo Harmonic simulation, Nav2 navigation stack, 3D depth perception pipeline, AMCL self-localization, pre-configured RViz 2 layout, and the BVR Mission Control Dashboard server.
- **`city_4wd_demo.launch.py`**:
  Advanced 4WD skid-steer simulation launcher designed for high-density outdoor city environments (`city_normal.sdf` or `trishul_final.sdf`). Automatically integrates SLAM Toolbox online mapping, 4WD Nav2 configuration, and YOLO real-time tactical decision engine.

### 2. BVR Tactical Mission Control Web Server (`dashboard_server.py`)
A high-throughput, multi-threaded `rclpy` node combined with a Python `ThreadingHTTPServer` running at **`http://127.0.0.1:8090`**:
- **Real-Time Telemetry Aggregation**: Streams robot pose (`map` frame), linear/angular velocity, battery telemetry (26.4V 6S LiPo), closest obstacle distance, and active YOLO hazard status at 30 Hz.
- **Multi-Camera MJPEG Streaming**: Provides high-frame-rate streams for 3D Depth Thermal Heatmap (`/stream/depth`), Tactical AI YOLO HUD (`/stream/yolo`), Forward Stereo Optical (`/stream/optical`), and Physical Rear Optical Camera (`/stream/rear`).
- **Interactive 2D SLAM Radar & Dynamic Goal Dispatcher**: Converts ROS 2 `/map` (`nav_msgs/OccupancyGrid`) to a dynamic transparent PNG overlay with laser scan points and enables one-click autonomous waypoint dispatch via the Nav2 `NavigateToPose` action client.
- **Authoritative Hardware E-STOP Clamp**: Immediately clamps `/cmd_vel` to zero and cancels active Nav2 action goals when triggered.
- **10m Panoramic Area Scan Routine**: Automated 360-degree sector sweep that expands the known SLAM occupancy map.
- **Dynamic Speed Calibration**: Allows real-time scaling of vehicle maximum cruising velocity via HTTP REST (`/api/speed_limit`).

### 3. Tactical GCS Web Frontend (`web/`)
- **`index.html`**: Tactical dark-mode glassmorphism interface with HUD telemetry banner, video viewport with Picture-in-Picture (PiP), interactive radar canvas, teleoperation D-pad, and mission event logger.
- **`css/dashboard.css`**: Professional cyber-defense visual styling, neon cyan/amber/red indicators, and responsive grid layouts.
- **`js/dashboard.js`**: Dynamic JavaScript client managing coordinate translations, live polling, dual-stream PiP swapping, keyboard driving (`W/A/S/D/Space`), and mission dispatch.

---

## 📡 REST & Streaming API Reference

| Endpoint | Method | Format | Description |
| :--- | :---: | :--- | :--- |
| **`/`** | `GET` | `text/html` | Serves the main Mission Control Web Dashboard. |
| **`/api/state`** | `GET` | `JSON` | Full snapshot: pose, velocities, battery, obstacle distance, YOLO decision, and map metadata. |
| **`/api/map`** | `GET` | `PNG` | Dynamic RGBA base64/PNG rendering of `/map` occupancy grid. |
| **`/stream/video`** | `GET` | `MJPEG` | Tactical AI HUD stream with YOLO detection boxes and decision telemetry. |
| **`/stream/depth`** | `GET` | `MJPEG` | RealSense 3D depth perception heatmap (`cv2.COLORMAP_TURBO`). |
| **`/stream/optical`** | `GET` | `MJPEG` | Forward stereo RGB optical camera stream. |
| **`/stream/rear`** | `GET` | `MJPEG` | Physical rear safety camera optical stream. |
| **`/api/goal`** | `POST` | `JSON` | Dispatches autonomous Nav2 waypoint goal `{"x": float, "y": float, "yaw": float}`. |
| **`/api/cancel`** | `POST` | `JSON` | Cancels active Nav2 navigation mission. |
| **`/api/teleop`** | `POST` | `JSON` | Drives robot directly via linear & angular velocity commands. |
| **`/api/estop`** | `POST` | `JSON` | Latches emergency stop; immediately zeroes velocity. |
| **`/api/reset_estop`** | `POST` | `JSON` | Releases E-STOP latch and restores drive capability. |
| **`/api/speed_limit`** | `POST` | `JSON` | Calibrates vehicle speed limit `{"speed": float}`. |
| **`/api/scan_10m`** | `POST` | `JSON` | Initiates 10-meter panoramic area sweep routine. |

---

## 🛠️ Execution

To launch the complete system with the master launcher:
```bash
# Using the root demo runner (interactive profile selection):
./run_demo.sh

# Or directly with ros2 launch:
ros2 launch trishul_bringup demo.launch.py
```
Open **`http://127.0.0.1:8090`** in any modern web browser.
