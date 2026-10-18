# Team Roles and Individual Work Guide

Five members work in one shared repository. Each person owns a module, but everyone should understand the overall data flow.

## Member 1 — Simulation and robot setup

**Owns:** `src/trishul_description/` and `src/trishul_simulation/`

### Main work
- Set up and document the robot model.
- Create or configure an outdoor-like Gazebo world.
- Add the simulated camera and any selected range/odometry sensors.
- Check robot movement and sensor output.
- Document launch commands and required packages.

### Install/learn
- Ubuntu 24.04 through WSL 2
- ROS 2 Jazzy
- Compatible Gazebo Harmonic integration
- Git
- Robot description basics (URDF/SDF), topics and transforms

### Deliver
- World and robot configuration.
- Reproducible launch procedure.
- List of sensor topics and message types.
- Evidence that another team member can launch it.

### Done when
The world launches, the robot moves, and required sensor topics publish data without undocumented manual fixes.

---

## Member 2 — Camera vision and AI

**Owns:** `src/trishul_perception/` and `requirements/vision.txt`

### Main work
- Subscribe to the agreed camera image topic.
- Process images using OpenCV.
- Try a lightweight pretrained detector if time and performance allow.
- Publish detections using the agreed message format.
- Explain limitations: a bounding box is not automatically a distance estimate or traversability map.

### Install/learn
- Git and Python
- OpenCV
- ROS 2 image tools and `cv_bridge` for ROS integration
- Model dependencies only after choosing the model
- ROS 2 Jazzy environment if the node runs as a ROS 2 package

### Deliver
- Perception node and dependency list.
- Sample outputs/screenshots.
- Test command and expected behavior.
- Notes on model source, license and resource use.

### Done when
The node receives the agreed image type, processes frames and publishes inspectable output. If the model is not ready, provide a working OpenCV baseline and report the limitation.

---

## Member 3 — Localization and mapping

**Owns:** `src/trishul_localization/`

### Main work
- Establish a baseline map/localization setup.
- Coordinate odometry, frames and map outputs with Members 1 and 4.
- Investigate visual odometry or visual SLAM only after the baseline is stable.
- Document the actual sensor inputs used.

### Install/learn
- Ubuntu, ROS 2 Jazzy and Git
- Mapping/localization concepts
- SLAM Toolbox for a range-sensor baseline if selected
- Visual SLAM dependencies only if approved and feasible

### Deliver
- Configuration and launch integration.
- Map/pose output verification steps.
- Coordinate-frame notes.
- Honest explanation of whether localization is range-sensor-based, visual, or combined.

### Done when
Pose/map output is repeatable and the navigation module can consume the agreed outputs.

---

## Member 4 — Navigation and obstacle avoidance

**Owns:** `src/trishul_navigation/`

### Main work
- Configure Nav2 for the selected robot.
- Set up goal navigation, cost maps and obstacle avoidance.
- Coordinate map, sensor and transform inputs with Members 1 and 3.
- Test multiple goal/obstacle scenarios.
- Record failures as well as successes.

### Install/learn
- Ubuntu, ROS 2 Jazzy and Git
- Nav2
- Cost-map and planner basics
- ROS 2 actions, topics and launch files

### Deliver
- Navigation configuration.
- Goal test instructions.
- Test summary and known limitations.

### Done when
The robot can receive a goal and complete the agreed baseline navigation trials, with results recorded.

---

## Member 5 — Integration, testing and demo

**Owns:** `src/trishul_bringup/`, `tests/`, `scripts/` and coordinates `docs/`

### Main work
- Keep the repository workflow healthy.
- Agree on interfaces with all module owners.
- Create the top-level launch workflow.
- Test the full system on the demo laptop.
- Review pull requests and help debug integration failures.
- Maintain setup instructions, demo steps, results and backup recording.

### Install/learn
- Full shared software stack early in the project
- Git/GitHub pull requests
- ROS 2 launch files, YAML configuration, logs and tests

### Deliver
- Reproducible bringup launch.
- Integration checks.
- Clean-clone setup instructions.
- Demo script and test summary.

### Done when
A clean clone can be built and the full demo can be run using documented commands. This member must also code and test; this is not a presentation-only role.

---

## Shared rules
- Each member can read all modules, but each module has a primary owner.
- Coordinate edits to shared files.
- Do not create duplicate robot descriptions or competing launch entry points.
- Test before pushing.
- Use a pull request before merging into `main`.
- Update documentation when commands, interfaces or dependencies change.
