# Testing Plan and Hackathon Demo

## 1. Test in layers

Do not wait until the end to test the whole project.

### Layer A — Simulation
- [ ] Gazebo world launches.
- [ ] Robot appears in the expected location.
- [ ] Robot can move.
- [ ] Camera and selected sensor topics publish data.

### Layer B — Perception
- [ ] Vision node starts.
- [ ] It receives the agreed camera image type.
- [ ] Image processing/detections can be inspected.
- [ ] Errors are visible in logs.
- [ ] Model dependency and weight setup is documented.

### Layer C — Localization
- [ ] Map or pose output appears.
- [ ] Pose changes as the robot moves.
- [ ] Coordinate frames are correct for the selected setup.
- [ ] The method used is documented honestly.

### Layer D — Navigation
- [ ] A goal can be sent.
- [ ] Robot attempts to reach the goal.
- [ ] Obstacle behavior is tested.
- [ ] Success and failure states are recorded.

### Layer E — Full integration
- [ ] Full launch starts required components.
- [ ] No required manual edits are needed after cloning.
- [ ] Gazebo, ROS 2 nodes and RViz work together.
- [ ] The demo works after a fresh terminal/session.
- [ ] The tested commit is recorded.

## 2. Test scenarios

Start with simple scenarios and increase difficulty:
1. Open area, short goal.
2. One obstacle on the direct route.
3. Multiple obstacles.
4. A goal requiring a route around an obstacle.
5. A perception scene with a visible object/hazard.
6. Repeat trials to check consistency.

Record the scenario, expected behavior, actual result, collision count, goal completion and notes.

## 3. Results table

| Run | Scenario | Goal reached? | Collision? | Perception output? | Localization method | Notes |
|---|---|---|---|---|---|---|
| 1 | To be tested | Pending | Pending | Pending | To be recorded | |
| 2 | To be tested | Pending | Pending | Pending | To be recorded | |
| 3 | To be tested | Pending | Pending | Pending | To be recorded | |

Do not fill in success claims until the test is run.

## 4. Suggested judging demo

1. Introduce Trishul and the outdoor navigation problem.
2. Show Gazebo and identify Point A and Point B.
3. Show the camera feed and explain what the AI can detect.
4. Show the map and estimated pose, stating which localization method is used.
5. Send a navigation goal.
6. Show autonomous movement and an obstacle-avoidance/replanning scenario.
7. Show actual test results and known limitations.
8. Explain what is implemented now and what remains future work.

## 5. Screen layout

On the demo laptop, show:
- Gazebo: 3D world and robot.
- RViz 2: map, pose, sensors and path.
- Camera/detection view if it adds useful evidence.
- Terminal/log/status view only when it helps explain behavior.

A simple, stable display is better than a complex dashboard that is difficult to maintain.

## 6. Demo reliability

- Freeze features before the final rehearsal.
- Test the exact laptop and launch command used for judging.
- Keep a backup recorded video; label it as recorded if used.
- Keep a known-good Git tag or commit.
- Do not rely on network access for required assets during the live demo if they can be prepared beforehand.
- Prepare short answers about sensors, localization, safety limitations and what is genuinely vision-based.
