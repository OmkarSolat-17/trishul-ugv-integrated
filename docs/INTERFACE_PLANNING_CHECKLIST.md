# Interface Planning Checklist

> **Purpose**: This checklist serves as an architectural template for the 5 leads to define and freeze message contracts, topic names, services, and TF frames before implementation begins.
>
> ⚠️ **Note**: Topic names, message schemas, and frame IDs below are conceptual placeholders to guide discussion. The team must formally agree on and document the final contracts before writing code.

---

## 1. Coordinate Frames & Conventions (REP Compliance)

Before writing any URDF or ROS 2 node, all leads must align with ROS Enhancement Proposals (REPs):
- [ ] **REP-103**: Standard Units of Measure & Coordinate Conventions (SI units: meters, radians, seconds; axes: X forward, Y left, Z up).
- [ ] **REP-105**: Coordinate Frames for Mobile Platforms:
  - [ ] `earth` (optional, for GPS/georeferencing)
  - [ ] `map` (world-fixed, drift-free, discontinuous jumps allowed from localization updates)
  - [ ] `odom` (world-fixed, continuous, smooth, subject to drift)
  - [ ] `base_link` (rigidly attached to robot chassis)
  - [ ] `base_footprint` (2D ground projection of `base_link`)
  - [ ] Sensor optical frames (e.g., `camera_link` vs `camera_optical_frame` where Z is forward, X is right, Y is down per image standards).

---

## 2. Sensor & Simulation Bridges (`trishul_description` & `trishul_simulation`)

- [ ] **Camera Sensor Interface**:
  - [ ] Image format: RGB8 vs BGR8 vs compressed
  - [ ] Sensor resolution and target framerate (FPS)
  - [ ] Camera info topic (intrinsic calibration matrix `K`, distortion parameters `D`)
  - [ ] Optical frame publishing in TF tree
- [ ] **Secondary Sensors** (to be decided by team):
  - [ ] Wheel odometry / joint states
  - [ ] IMU (linear acceleration, angular velocity, orientation)
  - [ ] Depth / LiDAR (if selected for obstacle detection)
- [ ] **Gazebo Harmonic Bridge (`ros_gz_bridge`)**:
  - [ ] List of Gazebo transport topics to bridge into ROS 2
  - [ ] Directionality of bridges (GZ -> ROS for sensors; ROS -> GZ for velocity commands `/cmd_vel`)
  - [ ] QoS profiles (SensorData QoS / Best Effort vs Reliable)

---

## 3. Vision & AI Perception (`trishul_perception`)

- [ ] **Input Subscription**:
  - [ ] Subscribes to raw camera image + camera info
  - [ ] Synchronization strategy (e.g., `message_filters` if stereo or multi-modal)
- [ ] **Hazard & Object Detection Output**:
  - [ ] Output format: 2D bounding boxes (e.g., `vision_msgs/Detection2DArray`), segmentation masks, or 3D obstacle markers (`visualization_msgs/MarkerArray`)
  - [ ] Confidence threshold parameterization
- [ ] **Traversability & Costmap Feed**:
  - [ ] Will perception publish an occupancy grid, a costmap plugin layer, or point cloud of detected obstacles?
  - [ ] Publishing frequency and latency targets (budgeting inference time)

---

## 4. Localization & Mapping (`trishul_localization`)

- [ ] **State Estimation Strategy**:
  - [ ] Odometry fusion package selection (e.g., `robot_localization` EKF vs native SLAM)
  - [ ] Inputs to EKF: Wheel odometry + IMU + Visual odometry
- [ ] **Visual SLAM / Localization Target**:
  - [ ] Candidate evaluation (e.g., RTAB-Map, ORB-SLAM3, Isaac ROS VSLAM, or pure visual odometry)
  - [ ] Map representation: 2D Occupancy Grid (`nav_msgs/OccupancyGrid`) vs 3D point cloud / octree
  - [ ] TF broadcasting responsibility: Which node broadcasts `map -> odom`? (Strict rule: only one node may broadcast a given TF transform!)
  - [ ] Relocalization / initial pose interface (`geometry_msgs/PoseWithCovarianceStamped`)

---

## 5. Autonomous Navigation & Obstacle Avoidance (`trishul_navigation`)

- [ ] **Nav2 Stack Configuration**:
  - [ ] Global Costmap layers (static layer from map, obstacle layer from vision/sensors, inflation layer)
  - [ ] Local Costmap layers (rolling window, real-time perception obstacle feeds)
  - [ ] Global Planner algorithm selection (e.g., NavFn, Smac Planner 2D/Lattice)
  - [ ] Local Controller algorithm selection (e.g., DWB, Regulated Pure Pursuit, MPPI)
  - [ ] Behavior Tree (BT) navigator XML and recovery behaviors
- [ ] **Actuation Command Interface**:
  - [ ] Output velocity command topic (`geometry_msgs/msg/Twist` or `geometry_msgs/msg/TwistStamped`)
  - [ ] Max linear speed (m/s), max angular speed (rad/s), acceleration limits
  - [ ] Emergency stop (E-stop) behavior / cancel goal handling

---

## 6. System Bringup & Diagnostics (`trishul_bringup`)

- [ ] **Unified Launch Architecture**:
  - [ ] Modular launch inclusion hierarchy:
    `trishul_bringup.launch.py` -> includes `simulation.launch.py`, `perception.launch.py`, `localization.launch.py`, `navigation.launch.py`
  - [ ] Launch arguments: `use_sim_time:=true/false`, `rviz:=true/false`, `world:=<path>`
- [ ] **Visualization**:
  - [ ] RViz 2 default configuration profile saved in `trishul_bringup/rviz/`
  - [ ] Displays: RobotModel, TF tree, Camera feed, Detections, Map, Global/Local Costmaps, Planned Path, Goal Pose
- [ ] **System Health & Verification**:
  - [ ] Verification checklist before demonstration
  - [ ] Logging conventions and ros2 diagnostic topics
