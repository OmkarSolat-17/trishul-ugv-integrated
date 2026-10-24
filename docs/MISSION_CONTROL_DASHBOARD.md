# Trishul UGV: Mission Control Web Dashboard

The **Trishul UGV Mission Control Web Dashboard** is a unified, browser-based Beyond Visual Range (BVR) ground control station (GCS) engineered for real-time telemetry inspection, autonomous goal dispatching, visual object detection monitoring, dynamic speed calibration, and safety operations for the Trishul autonomous UGV.

---

## 1. System Architecture & Components

The dashboard follows a decoupled client-server architecture built directly into the ROS 2 ecosystem:

```
+-------------------------------------------------------------------------------------------------------+
|                                              ROS 2 NODES                                              |
|  /ugv/combined/image (or /ugv/yolo/image)   /map (OccupancyGrid)   /odom   /scan   /ugv/perception/*  |
+---------------------------------------------------+---------------------------------------------------+
                                                    | Subscriptions & Action Client
                                                    v
+-------------------------------------------------------------------------------------------------------+
|                        Backend: trishul_dashboard_server (dashboard_server.py)                        |
|  - Built on rclpy MultiThreadedExecutor + Python ThreadingHTTPServer on 127.0.0.1:8090                |
|  - Real-time Nav2 Action Client (NavigateToPose) with distance remaining and ETA feedback             |
|  - Authoritative E-STOP safety clamp (publishes continuous zero-velocity to /cmd_vel)                 |
|  - Dynamic OccupancyGrid-to-RGBA image converter with dilated walls and transparent floors           |
|  - MJPEG video feed multiplexer (Depth Heatmap, YOLO AI HUD, Stereo Optical, Rear Camera)            |
|  - REST endpoints for 10m Panoramic Area Scan (/api/scan_10m) and Speed Calibration (/api/speed_limit)|
+---------------------------------------------------+---------------------------------------------------+
                                                    | REST API & MJPEG Stream (Port 8090)
                                                    v
+-------------------------------------------------------------------------------------------------------+
|                        Frontend Web Client (HTML5 / Vanilla CSS / Modern JS)                          |
|  - index.html: Tactical layout (HUD, Video Feed with PiP, 2D Radar Canvas, Detection Chips, Event Log)|
|  - dashboard.css: Glassmorphism theme, CSS grid, glowing indicators, cyber-defense aesthetics         |
|  - dashboard.js: Real-time polling, canvas coordinate transforms, goal dispatch, keyboard driving     |
+-------------------------------------------------------------------------------------------------------+
```

---

## 2. Source Code & Asset Locations

All dashboard files are located inside the `trishul_bringup` ROS 2 package:

| Component | Path | Description |
| :--- | :--- | :--- |
| **Backend Node** | [src/trishul_bringup/trishul_bringup/dashboard_server.py](../src/trishul_bringup/trishul_bringup/dashboard_server.py) | ROS 2 Python node serving HTTP REST endpoints, MJPEG video, and Nav2 action bridge. |
| **HTML UI** | [src/trishul_bringup/web/index.html](../src/trishul_bringup/web/index.html) | Modern dark-mode layout with HUD status bar, canvas map, video stream, and controls. |
| **CSS Styling** | [src/trishul_bringup/web/css/dashboard.css](../src/trishul_bringup/web/css/dashboard.css) | Custom styling, glassmorphism card panels, tactical HUD fonts, and micro-animations. |
| **JavaScript Client** | [src/trishul_bringup/web/js/dashboard.js](../src/trishul_bringup/web/js/dashboard.js) | Client logic managing state polling, canvas click-to-nav, feed switching, and E-STOP. |
| **Launch File** | [src/trishul_bringup/launch/demo.launch.py](../src/trishul_bringup/launch/demo.launch.py) | Master orchestrator launch file with configurable `dashboard_port` (default: 8090). |

---

## 3. Network Configuration & Endpoints

### Port Assignment: 8090
* **Default Port:** 8090
* **Local Web Address:** [http://127.0.0.1:8090](http://127.0.0.1:8090) or [http://localhost:8090](http://localhost:8090)
* *Architectural Note:* Port 8080 was intentionally avoided because Windows host machines often run background services that conflict with port 8080.

### HTTP REST & Streaming API Reference

| Endpoint | Method | Payload / Response | Purpose |
| :--- | :---: | :--- | :--- |
| **`/`** | `GET` | HTML | Serves the main web dashboard interface (`index.html`). |
| **`/api/state`** | `GET` | JSON | High-frequency telemetry: pose (x, y, yaw), velocity, battery, closest obstacle, Nav2 state, ETA, YOLO decision, and detections. |
| **`/stream/video`** | `GET` | Multipart MJPEG | Live video stream from Tactical AI HUD (`/ugv/yolo/image` or `/ugv/combined/image`). |
| **`/stream/depth`** | `GET` | Multipart MJPEG | Live 3D Depth perception heatmap (`cv2.COLORMAP_TURBO`). |
| **`/stream/optical`** | `GET` | Multipart MJPEG | Live forward stereo RGB camera stream. |
| **`/stream/rear`** | `GET` | Multipart MJPEG | Live physical rear safety camera stream. |
| **`/api/map`** | `GET` | PNG Image + Headers | Live 2D occupancy grid rendered from ROS 2 `/map` topic with origin and resolution headers. |
| **`/api/estop`** | `POST` | `{"status": "ok"}` | Engages Authoritative E-STOP: zeroes `/cmd_vel` continuously and cancels active Nav2 goals. |
| **`/api/reset_estop`** | `POST` | `{"status": "ok"}` | Resets E-STOP latch and restores drive authorization. |
| **`/api/goal`** | `POST` | `{"status": "ok"}` | Dispatches autonomous Nav2 `NavigateToPose` goal `{"x": float, "y": float, "yaw": float}`. |
| **`/api/cancel`** | `POST` | `{"status": "ok"}` | Cancels active Nav2 navigation mission. |
| **`/api/teleop`** | `POST` | `{"status": "ok"}` | Direct manual velocity control `{"linear": float, "angular": float}`. |
| **`/api/speed_limit`** | `POST` | `{"status": "ok"}` | Sets the vehicle default maximum velocity `{"speed": float}`. |
| **`/api/scan_10m`** | `POST` | `{"status": "ok"}` | Initiates 10-meter panoramic 360-degree environment mapping sweep. |

---

## 4. Key Interactive Capabilities

1. **Tactical 2D Radar Canvas (Click-to-Navigate)**:
   - Real-time map rendering from SLAM occupancy grid with dilated obstacle borders.
   - Interactive mouse click dispatches autonomous waypoints directly into Nav2.
   - Displays live robot footprint, heading vector, LiDAR beam hits, and active Nav2 global path plan.
2. **Picture-in-Picture (PiP) Dual Vision**:
   - Primary viewport displays full-screen tactical stream (e.g. YOLO AI HUD or 3D Depth Heatmap).
   - Secondary Picture-in-Picture window allows simultaneous rear or optical observation with one-click viewport swapping.
3. **Dynamic YOLO Decision Badge**:
   - Live visual indicator displaying the active perception decision (`BRAKE`, `YIELD`, or `CLEAR`) along with target class, distance, and commanded speed limit.
4. **Keyboard Teleoperation & Safety**:
   - Control vehicle with keyboard `W` (forward), `S` (reverse), `A` (turn left), `D` (turn right).
   - Instant Emergency Stop via `Spacebar` or on-screen E-STOP button.
