# TRISHUL — Member 3 Integration Guide

## 1. Quick Start (Gazebo Mode)
With Member 1's Gazebo running, launch:
  ros2 launch trishul_localization slam_launch.py use_sim_time:=true

## 2. Inputs Needed (From Member 1 - Gazebo)
- /camera/depth/image_raw (sensor_msgs/msg/Image)
- /camera/depth/camera_info (sensor_msgs/msg/CameraInfo)
- /clock (rosgraph_msgs/msg/Clock)
- /odom (nav_msgs/msg/Odometry)
- TF odom -> base_link (from Gazebo DiffDrive)
- TF base_link -> camera_link (from URDF / robot_state_publisher)

Note: Frame names must match: base_link and camera_link.

## 3. Outputs Provided (To Member 4 - Navigation)
- /map (nav_msgs/msg/OccupancyGrid, resolution 0.05m)
- map -> odom TF (from SLAM Toolbox)
- /scan (sensor_msgs/msg/LaserScan)

## 4. Important Rules for Member 4 (Nav2)
1. DO NOT launch AMCL. Live SLAM Toolbox handles localization.
2. DO NOT launch map_server. SLAM Toolbox publishes live /map.
3. Configure Nav2 frames: global_frame: map, robot_base_frame: base_link.

## 5. Troubleshooting
- Missing /map: SLAM takes ~10s to configure & activate.
- Jittery Robot: Make sure AMCL is OFF and static_transform_publisher is killed.
- Queue Full Warning: URDF is missing base_link -> camera_link transform.
