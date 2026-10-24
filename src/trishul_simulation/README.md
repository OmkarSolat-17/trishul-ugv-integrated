# trishul_simulation: Gazebo Harmonic Simulation & Physics Environment

[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6F00.svg)](https://gazebosim.org/docs/harmonic)
[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)

The **`trishul_simulation`** package provides the physics-based virtual proving grounds for the Trishul UGV platform within **Gazebo Harmonic**. It configures realistic outdoor simulation worlds, sensor parameter bridges, and 4WD vehicle physics.

---

## 🌍 Simulation Capabilities

1. **High-Fidelity Outdoor Worlds**:
   - **`worlds/city_normal.sdf`**: Complex urban outdoor environment featuring asphalt roadways, multi-level buildings, trees, streetlights, barriers, and dynamic pathways.
   - **`worlds/trishul_final.sdf`**: Advanced proving ground featuring elevated flyovers, bridges, rivers, ramp inclines, construction obstacles, and challenging terrain.
   - **TB3 Sandbox World**: Standard controlled proving ground for indoor/structured baseline navigation.

2. **4WD Skid-Steer Vehicle Model (`models/trishul_4wd_ugv`)**:
   - Four-wheel independent drive physics with realistic friction and slip coefficients.
   - Sensor payload: Forward RGB-D depth camera, physical rear optical camera, 360° LiDAR scanner (`base_scan`), and high-rate 6-DOF IMU.

3. **Bidirectional ROS-GZ Parameter Bridge (`config/ros_gz_bridge.yaml`)**:
   Seamlessly translates between Gazebo Harmonic native transport topics and ROS 2 Jazzy message types:
   - `/clock` (`rosgraph_msgs/msg/Clock`)
   - `/tf` (`tf2_msgs/msg/TFMessage`)
   - `/scan` (`sensor_msgs/msg/LaserScan`)
   - `/odom` (`nav_msgs/msg/Odometry`)
   - `/cmd_vel` (`geometry_msgs/msg/Twist`)
   - `/camera/image_raw` (`sensor_msgs/msg/Image`)
   - `/ugv/depth/image` (`sensor_msgs/msg/Image`)
   - `/ugv/rear_camera/image` (`sensor_msgs/msg/Image`)

---

## ⚡ Quickstart

Launch simulation independently:
```bash
ros2 launch trishul_simulation simulation.launch.py world:=city_normal.sdf
```
