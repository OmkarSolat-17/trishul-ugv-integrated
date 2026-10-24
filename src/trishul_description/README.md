# trishul_description: Physical Model & Kinematic Definitions

[![URDF](https://img.shields.io/badge/URDF-Xacro-orange.svg)]()
[![REP-105](https://img.shields.io/badge/Standards-REP--103%20%7C%20REP--105-blue.svg)]()

The **`trishul_description`** package contains the complete kinematic, physical, and sensor models for the Trishul autonomous Unmanned Ground Vehicle (UGV).

---

## 🚜 Robot Specifications & Kinematics

- **Chassis Architecture**:
  - High-traction 4WD Skid-Steer / Differential Drive platform.
  - Realistic inertial tensors, masses, and wheel friction properties optimized for rugged terrain, pavement, bridges, and flyovers.
- **Sensor Rig**:
  - **Forward Intel RealSense RGB-D**: Forward-facing perception camera delivering color optical frames and aligned depth matrices (`camera_link` / `camera_optical_frame`).
  - **Rear Optical Camera**: Integrated rear-facing camera (`rear_camera_link`) providing situational awareness and reverse navigation safety.
  - **360° 2D LiDAR Scanner**: Mounted at `base_scan` providing 12-meter 360-degree laser range finding at 10 Hz.
  - **6-DOF IMU**: High-frequency orientation and angular velocity estimation (`imu_link`).
  - **High-Resolution Wheel Encoders**: Generating continuous wheel odometry.

---

## 📐 Coordinate Frame Conventions (REP-105)

```
  map (Global SLAM / AMCL frame)
   └── odom (Continuous wheel odometry frame)
        └── base_footprint (Ground plane projection)
             └── base_link (Robot geometric origin)
                  ├── base_scan (360 LiDAR scanner)
                  ├── camera_link -> camera_optical_frame (RGB-D)
                  ├── rear_camera_link (Rear visual sensor)
                  ├── wheel_front_left_link / wheel_front_right_link
                  └── wheel_rear_left_link / wheel_rear_right_link
```
