# Trishul UGV Architecture Overview

This document outlines the modular system architecture for the Trishul autonomous UGV. It illustrates the data flow, separation of concerns, and integration points across the 5 core modules.

---

## 1. High-Level Modular Architecture

```mermaid
graph TD
    subgraph Simulation Layer ["1. Simulation Layer (Lead: Simulation)"]
        GZ["Gazebo Harmonic Engine\n(Physics, Outdoor World, Terrain)"]
        URDF["Robot Model (URDF/Xacro)\n(Kinematics, Collision, Inertia)"]
        BRIDGE["ros_gz_bridge\n(Clock, Camera, Odometry, Telemetry)"]
        GZ <--> BRIDGE
        URDF --> GZ
    end

    subgraph Perception Layer ["2. Perception & AI (Lead: Vision/AI)"]
        CAM["Raw Camera Images\n& Camera Info"]
        AI["AI Perception Node\n(Hazard Detection / Object Classification)"]
        TRAV["Traversability / Obstacle Cost Estimation"]
        BRIDGE --> CAM
        CAM --> AI
        AI --> TRAV
    end

    subgraph Localization Layer ["3. Localization & Mapping (Lead: Localization)"]
        ODOM["Wheel / IMU Odometry"]
        VSLAM["Visual SLAM / Odometry Pipeline"]
        FUSION["State Estimation / TF Broadcaster\n(Broadcasts odom -> base_link, map -> odom)"]
        BRIDGE --> ODOM
        CAM --> VSLAM
        ODOM --> FUSION
        VSLAM --> FUSION
    end

    subgraph Navigation Layer ["4. Navigation & Control (Lead: Navigation)"]
        COSTMAP["Nav2 Costmaps\n(Global & Local Rolling Windows)"]
        PLANNER["Nav2 Global Planner\n(Point A -> Point B Path Planning)"]
        CONTROLLER["Nav2 Local Controller\n(Dynamic Obstacle Avoidance)"]
        TRAV --> COSTMAP
        FUSION --> COSTMAP
        COSTMAP --> PLANNER
        PLANNER --> CONTROLLER
        FUSION --> CONTROLLER
    end

    subgraph Bringup & Integration ["5. Bringup & Diagnostics (Lead: Integration)"]
        LAUNCH["System Launch Architecture\n(Modular orchestration)"]
        RVIZ["RViz 2 Visualization\n(Sensors, Costmaps, Paths, Status)"]
        DIAG["Diagnostics & Test Harness"]
        CONTROLLER -->|Velocity Commands /cmd_vel| BRIDGE
        FUSION -.-> RVIZ
        COSTMAP -.-> RVIZ
        PLANNER -.-> RVIZ
        AI -.-> RVIZ
    end

    classDef sim fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:#1f2937;
    classDef perc fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:#1f2937;
    classDef loc fill:#e8f5e9,stroke:#388e3c,stroke-width:2px,color:#1f2937;
    classDef nav fill:#fff3e0,stroke:#f57c00,stroke-width:2px,color:#1f2937;
    classDef bring fill:#eceff1,stroke:#455a64,stroke-width:2px,color:#1f2937;

    class GZ,URDF,BRIDGE sim;
    class CAM,AI,TRAV perc;
    class ODOM,VSLAM,FUSION loc;
    class COSTMAP,PLANNER,CONTROLLER nav;
    class LAUNCH,RVIZ,DIAG bring;
```

---

## 2. Package Responsibilities & Boundaries

### 1. `trishul_description`
- **Owner**: Simulation Lead
- **Scope**: Contains 3D meshes, URDF/Xacro descriptions of the UGV chassis, wheels, sensor mounts, and joint kinematics.
- **Rules**: Must strictly define all visual, collision, and inertial properties. Must adhere to REP-103 and REP-105 for joint orientations and link frame names.

### 2. `trishul_simulation`
- **Owner**: Simulation Lead
- **Scope**: Gazebo Harmonic environment worlds (outdoor terrain, obstacles, uneven ground, lighting conditions), launch files for Gazebo Sim, and `ros_gz_bridge` configuration files.
- **Rules**: Responsible for translating Gazebo topics into standard ROS 2 message topics with correct QoS profiles.

### 3. `trishul_perception`
- **Owner**: Vision / AI Lead
- **Scope**: ROS 2 nodes processing camera feeds for object classification, hazard identification, and traversability analysis.
- **Rules**: Must keep inference latency deterministic to prevent lag in costmap updates. Must not directly send velocity commands (`cmd_vel`).

### 4. `trishul_localization`
- **Owner**: Localization Lead
- **Scope**: Spatial state estimation, coordinate frame transformations (`map -> odom -> base_link`), odometry fusion, and investigation/integration of visual SLAM.
- **Rules**: Only one node in the entire system may broadcast a given TF transform link (e.g. `odom -> base_link` or `map -> odom`). Avoid transform loops.

### 5. `trishul_navigation`
- **Owner**: Navigation Lead
- **Scope**: Nav2 configuration (planners, controllers, behavior trees, costmap plugin parameters).
- **Rules**: Subscribes to localization TF and perception obstacle layers; publishes motion commands (`cmd_vel`) to steer the vehicle.

### 6. `trishul_bringup`
- **Owner**: Integration Lead
- **Scope**: Top-level orchestration. Houses top-level launch files that allow booting the entire stack (or specific subsets for testing), centralized RViz 2 profiles, and parameter overrides.
- **Rules**: Does not contain core algorithm logic. Relies on launch inclusions of other packages.
