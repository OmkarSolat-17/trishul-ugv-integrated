# Interface Agreement

This document tracks frozen and active interface contracts across the Trishul UGV subsystems.

## Why this document matters

ROS 2 nodes can run separately and still fail to work together if they use different topic names, message types, coordinate frames or assumptions. Agree on the interfaces early.

## Interface table

| Data or action | Producer/owner | Consumer | Final topic/action/service | Message type | Frame or notes |
|---|---|---|---|---|---|
| Camera images | Member 1 (Simulation) | Member 2 (Perception) | `/camera/image_raw` | `sensor_msgs/msg/Image` | Frame: `camera_optical_frame` (Pending vision integration) |
| Range scan (LiDAR) | Member 1 (Simulation) | Member 4 (`trishul_navigation`) | `/scan` | `sensor_msgs/msg/LaserScan` | **Frozen**: `base_scan` (360° 2D LiDAR range scan) |
| Odometry | Member 1 (Simulation) | Member 3 / Member 4 | `/odom` | `nav_msgs/msg/Odometry` | **Frozen**: `odom -> base_footprint` |
| Transform tree | Simulation / Localization | Navigation / RViz | `/tf`, `/tf_static` | `tf2_msgs/msg/TFMessage` | **Frozen**: `map -> odom -> base_footprint -> base_link -> base_scan` |
| Map | Member 3 (Localization) | Member 4 / RViz | `/map` | `nav_msgs/msg/OccupancyGrid` | **Frozen**: Frame `map` (Static baseline grid) |
| Estimated robot pose | Localization (AMCL) | Navigation / RViz | `/initialpose` / `/amcl_pose` | `geometry_msgs/msg/PoseWithCovarianceStamped` | **Frozen**: Auto-initialized at `(-2.00, -0.50, 0.0)` |
| Navigation goal | Operator / Commander | Nav2 (`bt_navigator`) | `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | **Frozen**: Nav2 Action Server (`BasicNavigator`) |
| Velocity command | Member 4 (`trishul_navigation`) | Simulated robot | `/cmd_vel` | `geometry_msgs/msg/Twist` | **Frozen**: DWB output with active safety brake override |
| Perception detections | Member 2 (Perception) | Visualization / Nav | To be agreed | To be agreed | Define fields and confidence |
| Traversability output | Member 2 (Perception) | Nav Costmaps | To be agreed | To be agreed | Define representation and validation |
| Navigation status & Telemetry | Member 4 (`status_node`) | Bringup / Diagnostics | `trishul/status` | `std_msgs/msg/String` | **Frozen**: 1 Hz continuous system heartbeat |

## Decisions & Subsystem Status

- [x] **Robot base frame and sensor frames**: `base_link`, `base_footprint`, `base_scan` (REP-105 compliant).
- [ ] **Camera topic, image encoding and frame ID**: To be completed by Vision Lead.
- [x] **Range-sensor topic**: `/scan` (`sensor_msgs/msg/LaserScan`).
- [x] **Odometry topic and frame conventions**: `/odom` (`nav_msgs/msg/Odometry`, `odom -> base_footprint`).
- [x] **Map and localization outputs**: `/map` and AMCL filter with `set_initial_pose` at `(-2.00, -0.50)`.
- [x] **Navigation goal and status interface**: `/navigate_to_pose` Action and `trishul/status` 1 Hz heartbeat.
- [x] **Velocity command interface**: `/cmd_vel` (`geometry_msgs/msg/Twist`).
- [x] **Emergency stop behavior**: Active collision brake in `sensor_monitor` overrides `/cmd_vel` with `linear.x = 0.0` when forward obstacles are $< 0.25$ m.
- [ ] **Perception message type and fields**: To be completed by Vision Lead.
- [ ] **Whether detections affect navigation or are only displayed**: To be decided upon perception completion.
- [x] **Expected launch order and dependencies**: Unified single-command launch implemented in `trishul_navigation/launch/navigation.launch.py`.

## Change process

If an interface changes:
1. The owner explains why.
2. The owner updates this document and related configuration.
3. Affected module owners review the change.
4. The change is tested across the connected modules.
5. The pull request records the interface change.
