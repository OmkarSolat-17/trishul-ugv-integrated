# trishul_localization: State Estimation, SLAM & Frame Synchronization

[![SLAM Toolbox](https://img.shields.io/badge/SLAM-SLAM_Toolbox-blue.svg)](https://github.com/SteveMacenski/slam_toolbox)
[![AMCL](https://img.shields.io/badge/Localization-AMCL_Particle_Filter-brightgreen.svg)]()

The **`trishul_localization`** package provides robust state estimation, real-time SLAM (Simultaneous Localization and Mapping), and sub-millimeter TF2 frame synchronization for the Trishul UGV platform.

---

## 🗺️ Localization & Mapping Capabilities

1. **SLAM Toolbox Online Async Mapping (`slam_toolbox_online.yaml`)**:
   - Generates real-time 2D occupancy grids (`/map`) in complex outdoor city environments.
   - Solves pose-graph loop closures with sub-millimeter precision.
   - Dynamically broadcasts authoritative `map -> odom` transform updates.

2. **Adaptive Monte Carlo Localization (AMCL)**:
   - Robust probabilistic particle filter localization for mapped environments.
   - Pre-configured spawn alignment eliminating initial localization lag.

3. **TF2 Transform Broadcaster (`frame_broadcaster_node.py`)**:
   - Guarantees unbroken kinematic trees across all simulation and hardware components.
   - Synchronizes robot pose in real time between RViz 2 and the BVR Mission Control Web Dashboard.

4. **Visual Odometry & Depth-to-Laser Projection (`visual_odometry_node.py`, `depth_to_laserscan_node.py`)**:
   - Provides optical feature tracking and depth slice projection for environments where laser returns are unavailable.

---

## ⚡ Execution

Run SLAM mapping independently:
```bash
ros2 launch trishul_localization slam_launch.py use_sim_time:=true
```
