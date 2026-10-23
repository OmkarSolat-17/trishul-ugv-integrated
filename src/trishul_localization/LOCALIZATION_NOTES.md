# TRISHUL — Member 3 Localization & Mapping Notes

## Honest Localization Statement
TRISHUL localization is range-sensor-based. We convert simulated depth camera images into 2D laser scans (depthimage_to_laserscan), and feed them into SLAM Toolbox alongside wheel odometry. It does not rely on GPS.

Visual Odometry (/vo/odom) was implemented as an experimental auxiliary module (ORB feature tracking + IMU fusion). It is run in isolation and does not publish TF transforms to avoid frame conflicts.

## TF Ownership Tree
- map -> odom: Published ONLY by slam_toolbox
- odom -> base_link: Published ONLY by Gazebo DiffDrive
- base_link -> camera_link: Published ONLY by robot_state_publisher
