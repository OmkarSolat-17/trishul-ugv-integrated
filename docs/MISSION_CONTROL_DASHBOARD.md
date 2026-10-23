# Trishul UGV: Mission Control Web Dashboard

The **Trishul UGV Mission Control Web Dashboard** is a unified, browser-based ground control station (GCS) engineered for real-time telemetry inspection, autonomous goal dispatching, visual object detection monitoring, and safety operations for the Trishul autonomous UGV.

---

## 1. System Architecture & Components

The dashboard follows a decoupled client-server architecture built directly into the ROS 2 ecosystem:

`
+---------------------------------------------------------------------------------------+
|                                    ROS 2 NODES                                        |
|  /ugv/combined/image (or /camera/image_raw)   /map (OccupancyGrid)   /odom   /scan   |
+-------------------------------------------+-------------------------------------------+
                                            | Subscriptions & Action Client
                                            v
+---------------------------------------------------------------------------------------+
|             Backend: trishul_dashboard_server (dashboard_server.py)                   |
|  - Built on rclpy MultiThreadedExecutor + Python ThreadingHTTPServer                 |
|  - Real-time Nav2 Action Client (NavigateToPose) with distance & ETA feedback        |
|  - Authoritative E-STOP safety clamp (publishes continuous zero-velocity to /cmd_vel) |
|  - Dynamic OccupancyGrid-to-PNG renderer (OpenCV / numpy)                            |
|  - MJPEG video feed multiplexer                                                      |
+-------------------------------------------+-------------------------------------------+
                                            | REST API & MJPEG Stream (Port 8090)
                                            v
+---------------------------------------------------------------------------------------+
|             Frontend Web Client (HTML5 / Vanilla CSS / Modern JS v2)                  |
|  - index.html: Tactical layout (HUD, Video Feed, 2D Map Canvas, Detection Chips, Log)|
|  - dashboard.css: Glassmorphism theme, CSS grid, glowing indicators, responsive      |
|  - dashboard.js (v2): Real-time polling, canvas coordinate transforms, goal dispatch |
+---------------------------------------------------------------------------------------+
`

---

## 2. Source Code & Asset Locations

All dashboard files are located inside the 	rishul_bringup ROS 2 package:

| Component | Path | Description |
| :--- | :--- | :--- |
| **Backend Node** | [src/trishul_bringup/trishul_bringup/dashboard_server.py](../src/trishul_bringup/trishul_bringup/dashboard_server.py) | ROS 2 Python node serving HTTP REST endpoints, MJPEG video, and Nav2 action bridge. |
| **HTML UI** | [src/trishul_bringup/web/index.html](../src/trishul_bringup/web/index.html) | Modern dark-mode layout with HUD status bar, canvas map, video stream, and controls. |
| **CSS Styling** | [src/trishul_bringup/web/css/dashboard.css](../src/trishul_bringup/web/css/dashboard.css) | Custom styling, glassmorphism card panels, tactical HUD fonts, and micro-animations. |
| **JavaScript Client (v2)** | [src/trishul_bringup/web/js/dashboard.js](../src/trishul_bringup/web/js/dashboard.js) | Version 2 client logic managing state polling, canvas click-to-nav, and latched E-STOP. |
| **Launch File** | [src/trishul_bringup/launch/demo.launch.py](../src/trishul_bringup/launch/demo.launch.py) | Master orchestrator launch file with configurable launch_dashboard and dashboard_port. |

> **Backup & Build Scripts (Windows Antigravity Brain):**  
> C:\Users\Durgvijay Chauhan\.gemini\antigravity-ide\brain\be9c0aeb-d9d1-4852-8507-a7eacff22420\scratch\  
> (uild_html_v2.py, uild_js_v2.py, uild_server_v2.py, uild_css.py)

---

## 3. Network Configuration & Endpoints

### Port Assignment: 8090
* **Default Port:** 8090
* **Local Web Address:** [http://127.0.0.1:8090](http://127.0.0.1:8090) or [http://localhost:8090](http://localhost:8090)
* *Architectural Note:* Port 8080 was intentionally avoided because Windows host machines often run background services (such as Oracle Database TNSLSNR.EXE) that conflict with port 8080.

### HTTP REST & Streaming API Reference

| Endpoint | Method | Payload / Response | Purpose |
| :--- | :---: | :--- | :--- |
| / | GET | HTML | Serves the main web dashboard interface (index.html). |
| /api/state | GET | JSON | High-frequency telemetry: pose (x, y, yaw), velocity, battery, closest obstacle, Nav2 state, ETA, and detections. |
| /stream/video | GET | Multipart MJPEG | Live video stream from /ugv/combined/image (with auto-fallback to /camera/image_raw). |
| /api/map | GET | PNG Image + Headers | Live 2D occupancy grid rendered from ROS 2 /map topic with origin and resolution headers. |
| /api/estop | POST | {
