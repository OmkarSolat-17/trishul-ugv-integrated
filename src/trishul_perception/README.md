# trishul_perception: Vision-AI & Tactical Decision-Making Engine

[![YOLOv8](https://img.shields.io/badge/YOLO-Trained_Vision_AI-brightgreen.svg)]()
[![OpenCV](https://img.shields.io/badge/OpenCV-4.8+-red.svg)](https://opencv.org/)

The **`trishul_perception`** package provides high-rate visual processing, real-time object and hazard detection, 3D metric spatial extraction, and reactive route decision-making for autonomous operations.

---

## 🧠 Core Deliverables & Technologies

### 1. Vision-AI & YOLO Tactical Decision-Making Engine (`image_processor.py`)
- **Trained Deep Learning Inference**: Utilizes fine-tuned YOLO weights (`models/best.pt` or `models/yolo26n.pt`) with real-time inference on GPU or CPU. If deep learning packages are absent, it automatically engages an intelligent tactical computer vision depth-saliency fallback.
- **3D Spatial Metric Extraction**: Aligns 2D bounding boxes with registered RealSense depth maps to extract precise physical metrics:
  - Metric Distance $Z$ (meters)
  - Lateral Centerline Offset $X$ (meters)
  - Estimated 3D bounding envelope
- **Active Route Decision Matrix**:
  - **CRITICAL BRAKE (`< 1.8 m` in corridor)**: Immediately triggers vision-based safety brake to prevent imminent collisions.
  - **YIELD & SLOW (`1.8 m - 6.0 m` in corridor)**: Dynamically scales down vehicle speed limit via `/speed_limit` to ensure smooth obstacle negotiation.
  - **CLEAR CORRIDOR**: Restores nominal cruising speed once path is unobstructed.
- **PointCloud2 Nav2 Costmap Projection**:
  Projects 3D visual obstacle detections into dynamic `sensor_msgs/msg/PointCloud2` packets consumed directly by the Nav2 local costmap obstacle layer, prompting automatic global and local path replanning around unmapped hazards.
- **3D Depth Perception Thermal Heatmap**:
  Transforms raw depth frames into normalized, high-contrast thermal colormaps (`cv2.COLORMAP_TURBO`) at 30 FPS, publishing to `/ugv/combined/image` with tactical HUD telemetry overlays.

---

## 📡 Published & Subscribed Topics

| Topic | Type | Direction | Description |
| :--- | :--- | :---: | :--- |
| `/camera/image_raw` | `sensor_msgs/msg/Image` | Sub | Raw optical camera frames from Gazebo bridge. |
| `/camera/depth/image_raw` | `sensor_msgs/msg/Image` | Sub | Aligned depth stream from simulation RealSense. |
| `/ugv/combined/image` | `sensor_msgs/msg/Image` | Pub | Tactical HUD video with colormap depth and detection reticles. |
| `/ugv/perception/detections` | `std_msgs/msg/String` | Pub | JSON-formatted detection telemetry for dashboard HUD. |
| `/ugv/perception/decision` | `std_msgs/msg/String` | Pub | Reactive route decision (`EMERGENCY_STOP`, `YIELD_AND_SLOW`, `CLEAR`). |
| `/ugv/perception/obstacles_pc` | `sensor_msgs/msg/PointCloud2` | Pub | 3D obstacle point cloud projected to Nav2 costmap layers. |
| `/speed_limit` | `nav2_msgs/msg/SpeedLimit` | Pub | Dynamic speed limit commands published to Nav2 controller. |

---

## 🛠️ Execution

Launch perception node standalone:
```bash
ros2 launch trishul_perception perception.launch.py
```
