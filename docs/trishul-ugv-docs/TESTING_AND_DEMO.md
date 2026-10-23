# Testing Plan and Hackathon Demo

## 1. Test in layers

Do not wait until the end to test the whole project.

### Layer A — Simulation
- [x] Gazebo world launches (`turtlebot3_world` baseline).
- [x] Robot appears in the expected location (`X = -2.00, Y = -0.50`).
- [x] Robot can move (`/cmd_vel` motor actuation).
- [x] LiDAR and odometry sensor topics publish data (`/scan`, `/odom`, `/clock`).

### Layer B — Perception
- [ ] Vision node starts.
- [ ] It receives the agreed camera image type.
- [ ] Image processing/detections can be inspected.
- [ ] Errors are visible in logs.
- [ ] Model dependency and weight setup is documented.

### Layer C — Localization
- [x] Map or pose output appears (`/map`, `/amcl_pose`).
- [x] Pose changes as the robot moves.
- [x] Coordinate frames are correct (`map -> odom -> base_footprint -> base_link`).
- [x] The method used is documented honestly (AMCL baseline particle filter with auto-initialization).

### Layer D — Navigation (Delivered & Verified)
- [x] A goal can be sent (`mission_navigator`, custom coordinates CLI, RViz `Nav2 Goal`).
- [x] Robot attempts to reach the goal (Nav2 Smac/NavFn planners + DWB local controller).
- [x] Obstacle behavior is tested (dynamic costmap inflation + active safety brake at $< 0.25$ m).
- [x] Success and failure states are recorded (WSL tolerances tuned to 1.5s, BT server timeout set to 1000ms).

### Layer E — Full integration
- [x] Full launch starts required components (`ros2 launch trishul_navigation navigation.launch.py`).
- [x] No required manual edits needed after cloning (`colcon build --symlink-install`).
- [x] Gazebo, ROS 2 Nav2 nodes and RViz work together seamlessly.
- [x] The demo works reliably from a fresh terminal session.
- [x] The tested commit is recorded (`525bc2a` on branch `trishul-navigation`).

---

## 2. Test scenarios

Start with simple scenarios and increase difficulty:
1. Open area, short goal.
2. One obstacle on the direct route.
3. Multiple obstacles.
4. A goal requiring a route around an obstacle (Cross-arena traversal).
5. A perception scene with a visible object/hazard.
6. Repeat trials to check consistency.

---

## 3. Results table

| Run | Scenario | Goal reached? | Collision? | Sensor / Perception output? | Localization method | Notes |
|---|---|---|---|---|---|---|
| 1 | Baseline cross-arena traversal (`X: 1.80, Y: -0.50`) from spawn (`X: -2.00, Y: -0.50`) | **Yes** | 0 (None) | 360° LiDAR range scan (`/scan`) | AMCL (Auto-initialized at spawn) | Traversed arena with dynamic obstacle avoidance; safety monitor confirmed clearance. |
| 2 | Custom target coordinate navigation (`target_x:=1.0, target_y:=0.5`) | **Yes** | 0 (None) | 360° LiDAR range scan (`/scan`) | AMCL | DWB trajectory controller planned smooth arc around pillars. |
| 3 | Active emergency braking trial (obstacle intrusion $< 0.25$ m) | **Yes** (Braked) | 0 (Prevented) | Forward LiDAR sector detection | AMCL | `sensor_monitor` successfully dispatched emergency stop (`linear.x = 0.0`) to `/cmd_vel`. |

---

## 4. Suggested judging demo

1. Introduce Trishul and the outdoor navigation problem.
2. Show Gazebo and identify Point A (spawn at `-2.0, -0.5`) and Point B (opposite arena side at `1.8, -0.5`).
3. Show the map, costmap inflation layers, and AMCL localized pose in RViz 2.
4. Send an autonomous navigation goal using `ros2 run trishul_navigation mission_navigator`.
5. Show autonomous movement, real-time trajectory replanning around arena pillars, and active safety monitoring.
6. Show actual test results, quality assurance (`colcon test`: 0 errors, 0 failures), and WSL2 performance optimizations.
7. Explain what is implemented now (`trishul_navigation`) and future vision integration steps.

---

## 5. Screen layout

On the demo laptop, show:
- Gazebo Sim: 3D world and robot model.
- RViz 2: map, localized pose, costmaps, laser scan sectors, and planned path.
- Terminal 1: master launch output with telemetry heartbeat.
- Terminal 2: `mission_navigator` progress and ETA feedback.

---

## 6. Demo reliability

- Freeze features before the final rehearsal.
- Test the exact laptop and launch command used for judging.
- Keep a backup recorded video; label it as recorded if used.
- Keep a known-good Git tag or commit (`525bc2a`).
- Package passes all PEP8 (Flake8) and PEP257 docstring tests.
