# Trishul — Product and Project Specification

## 1. Project summary

**Name:** Trishul  
**Type:** Simulation-based autonomous navigation software for an Unmanned Ground Vehicle (UGV)  
**Team:** Five members  
**Target:** A short hackathon MVP, with nine days as the planning target  
**Primary demo machine:** The team's designated Dell G15 laptop, subject to testing  
**Status:** Planned; do not describe untested features as complete.

Trishul is intended to be the software “brain” of a UGV. It combines simulation, sensor communication, camera perception, localization, navigation and visualization so the robot can move toward a goal while responding to its surroundings.

## 2. Problem and hackathon context

The project is aligned with the problem statement identified in the project context as:

**“Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment”**  
**Organization:** Bharat Electronics Limited (BEL)  
**Problem Statement ID:** 26126

The problem concerns outdoor navigation when terrain is uneven or unpredictable, lighting changes, and GPS may be unreliable. The intended system should identify traversable ground and hazards, estimate its position without relying on GPS, and navigate toward a destination while avoiding collisions.

The team should verify the official event/problem-statement document before submitting claims, eligibility details, judging criteria, or official requirements. This guide does not invent an official scoring rubric.

## 3. Aim

Build a working simulation in which a UGV:
1. Starts at Point A.
2. Receives information from simulated sensors.
3. Processes camera images to identify objects or possible hazards.
4. Estimates its position using the chosen localization method.
5. Plans a route toward Point B.
6. Avoids obstacles in the supported test scenarios.
7. Reaches the goal, with its behavior visible to the team and judges.

## 4. What the team will build

### Core MVP
- Outdoor-like world and simulated robot in Gazebo.
- Simulated camera and the sensor inputs required by the selected baseline.
- ROS 2 communication between simulation and software modules.
- Mapping/localization baseline.
- Nav2 goal navigation and obstacle avoidance.
- RViz 2 visualization.
- A repeatable launch procedure and test record.

### Vision-focused target
- Camera image processing with OpenCV.
- A lightweight pretrained object/hazard detector, if feasible.
- A clearly documented method for deciding whether detections affect navigation.
- Camera-based visual localization or visual odometry as a stretch goal if integration time allows.

### Important technical honesty
A setup that uses SLAM Toolbox with simulated LiDAR/range scans may be a useful navigation baseline, but it does **not by itself** satisfy a camera-primary visual-navigation goal. Object detection alone does not provide reliable object distance or prove that terrain is safe. Camera-based localization and camera-derived traversability must be implemented and tested before claiming those features.

## 5. Why these tools?

- **Ubuntu through WSL 2:** provides a Linux development environment without replacing Windows or requiring a traditional full virtual machine.
- **ROS 2:** lets simulation, perception, localization and navigation exchange messages and commands.
- **Gazebo:** creates the virtual world, robot and simulated sensors.
- **Python/OpenCV/AI model:** processes images and identifies visual patterns.
- **Localization/SLAM:** estimates where the robot is and may build a map.
- **Nav2:** handles configured navigation goals, planning and obstacle avoidance.
- **RViz 2:** helps people inspect maps, poses, sensors and planned paths.
- **GitHub:** shares code and preserves the team's reviewed version.

## 6. Expected final result

The intended live demo should show:
1. A simulated outdoor world and UGV.
2. Point A and Point B.
3. Camera feed and any working detections.
4. A map and robot pose estimate, labelled with the actual method used.
5. Autonomous goal navigation.
6. An obstacle avoidance or replanning scenario.
7. A short test summary with successes, failures and limitations.

The demo should run on one laptop wherever possible. A projector or second display can show Gazebo and RViz side by side. Do not add multi-computer networking unless necessary.

## 7. Success measures

Record results rather than relying only on visual impressions:
- Number of goal trials attempted.
- Number of goals reached.
- Number of collisions.
- Approximate completion time.
- Whether the perception node received camera frames.
- Whether detections were produced in the tested scenes.
- Whether the localization output behaved as expected.
- Whether the full launch worked after a clean clone/build.

Set actual thresholds with the team after the baseline works. Do not invent results in advance.

## 8. Scope and constraints

- Simulation-only for the MVP.
- No claim of physical-robot testing.
- No claim of GPS-free visual localization unless the tested pipeline actually uses camera-based localization.
- No large model training from scratch.
- Prefer existing ROS 2/Nav2 capabilities over rebuilding a complete navigation stack.
- Prioritize a stable end-to-end demonstration over extra features.
