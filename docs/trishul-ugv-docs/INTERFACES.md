# Interface Agreement

This document must be filled in by the team before modules are integrated. Names below are categories to decide, not final topic names.

## Why this document matters

ROS 2 nodes can run separately and still fail to work together if they use different topic names, message types, coordinate frames or assumptions. Agree on the interfaces early.

## Interface table

| Data or action | Producer/owner | Consumer | Final topic/action/service | Message type | Frame or notes |
|---|---|---|---|---|---|
| Camera images | Member 1 | Member 2 | To be agreed | To be agreed | Confirm encoding and frame |
| Range scan, if used | Member 1 | Localization/navigation | To be agreed | To be agreed | Confirm sensor frame |
| Odometry | Simulation/robot setup | Localization/navigation | To be agreed | To be agreed | Confirm frame IDs |
| Transform tree | Robot/simulation and localization | Navigation/RViz | To be agreed | TF | Agree frame names |
| Map | Localization | Navigation/RViz | To be agreed | To be agreed | Confirm map frame |
| Estimated robot pose | Localization | Navigation/RViz | To be agreed | To be agreed | State source of estimate |
| Navigation goal | Operator/bringup | Nav2 | To be agreed | Action/interface | Record goal procedure |
| Velocity command | Navigation | Simulated robot | To be agreed | To be agreed | Confirm bridge/controller |
| Perception detections | Member 2 | Visualization or navigation | To be agreed | To be agreed | Define fields and confidence |
| Traversability output, if implemented | Member 2 | Navigation/perception integration | To be agreed | To be agreed | Define representation and validation |
| Navigation status | Nav2 | Bringup/demo | To be agreed | To be agreed | Show success/failure clearly |

## Decisions required

- [ ] Robot base frame and sensor frames
- [ ] Camera topic, image encoding and frame ID
- [ ] Range-sensor topic, if used
- [ ] Odometry topic and frame conventions
- [ ] Map and localization outputs
- [ ] Navigation goal and status interface
- [ ] Velocity command interface and Gazebo bridge/controller
- [ ] Perception message type and fields
- [ ] Whether detections affect navigation or are only displayed
- [ ] How missing/stale sensor data is handled
- [ ] Expected launch order and dependencies

## Change process

If an interface changes:
1. The owner explains why.
2. The owner updates this document and related configuration.
3. Affected module owners review the change.
4. The change is tested across the connected modules.
5. The pull request records the interface change.

Do not claim that object detections alter navigation unless the detection-to-cost-map or other navigation integration is implemented and tested.
