# Trishul UGV: Vision-Based Autonomous Navigation System

[![ROS 2](https://img.shields.io/badge/ROS_2-Jazzy_Jalisco-3498DB.svg)](https://docs.ros.org/en/jazzy/)
[![Gazebo](https://img.shields.io/badge/Gazebo-Harmonic-FF6F00.svg)](https://gazebosim.org/docs/harmonic)
[![Ubuntu](https://img.shields.io/badge/Ubuntu-24.04_LTS-E95420.svg)](https://ubuntu.com/)
[![WSL](https://img.shields.io/badge/WSL_2-Windows_11-0078D6.svg)](https://learn.microsoft.com/en-us/windows/wsl/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Problem Statement (BEL — ID 26126):** *Vision Based Autonomous Navigation for Unmanned Ground Vehicle for Outdoor Environment.*

---

## ⚠️ Current Project Status

> **STATUS: REPOSITORY SKELETON INITIALIZED — PRE-IMPLEMENTATION**
>
> All ROS 2 packages are empty placeholders. The robot model, simulation world, AI perception models, SLAM pipelines, and Nav2 controllers are **NOT yet implemented**. Empty directories are preserved by `.gitkeep` files. ROS 2 packages must be initialized using `ros2 pkg create` before any code is written.

---

## 1. Start Here — Reading Order for New Team Members

Every member should read these in order before touching any code:

1. **This file** — project overview and structure.
2. [docs/trishul-ugv-docs/PRODUCT.md](docs/trishul-ugv-docs/PRODUCT.md) — full project goal, hackathon context, scope, and success measures.
3. [docs/trishul-ugv-docs/TEAM_ROLES.md](docs/trishul-ugv-docs/TEAM_ROLES.md) — find your role and what you must deliver.
4. [docs/trishul-ugv-docs/SETUP_GUIDE.md](docs/trishul-ugv-docs/SETUP_GUIDE.md) — WSL 2, Ubuntu 24.04, ROS 2 Jazzy and Gazebo setup steps.
5. [docs/trishul-ugv-docs/GIT_WORKFLOW.md](docs/trishul-ugv-docs/GIT_WORKFLOW.md) — branching, commits, PRs, and what never to commit.
6. [docs/trishul-ugv-docs/INTERFACES.md](docs/trishul-ugv-docs/INTERFACES.md) — the interface agreement table; fill this in before connecting modules.
7. [docs/trishul-ugv-docs/TESTING_AND_DEMO.md](docs/trishul-ugv-docs/TESTING_AND_DEMO.md) — test layers, scenario checklists, and judging demo plan.
8. [docs/trishul-ugv-docs/AI_CODING_GUIDE.md](docs/trishul-ugv-docs/AI_CODING_GUIDE.md) — rules for using Antigravity or any AI coding assistant.
9. [docs/trishul-ugv-docs/CONTRIBUTING.md](docs/trishul-ugv-docs/CONTRIBUTING.md) — quick contributing reference card.

---

## 2. Project Overview

**Trishul** is the software "brain" of a simulated autonomous UGV engineered for rugged outdoor environments. It combines simulation, sensor communication, camera-based perception, localization, and navigation so the robot can move toward a goal while responding to its surroundings.

The team's **nine-day hackathon MVP** aims to demonstrate:

1. **Realistic Outdoor Simulation** — UGV operating in a Gazebo Harmonic outdoor world with realistic physics, terrain, and lighting.
2. **Sensor Suite Simulation** — Simulated cameras (monocular / RGB-D) and proprioceptive sensors (IMU, wheel encoders).
3. **Vision & AI Perception** — Camera-based image processing, lightweight AI hazard/obstacle detection, and traversability estimation.
4. **Mapping & Localization** — State estimation targeting **visual SLAM / visual odometry** as the primary localization source.
5. **Autonomous Navigation** — Point A → Point B goal navigation using the Nav2 stack.
6. **Dynamic Obstacle Avoidance** — Real-time costmap updates from visual perception with local replanning.
7. **Comprehensive Visualization** — Live telemetry, sensor feeds, costmaps, and trajectories in RViz 2 and Gazebo.
8. **Reproducible Demonstration** — Full end-to-end execution on one Dell G15 laptop (Windows 11 + WSL 2 + Ubuntu 24.04 LTS).

> **Technical honesty rule:** A setup that uses SLAM Toolbox with simulated LiDAR may be a useful baseline, but it does **not** satisfy a camera-primary visual-navigation goal. Camera-based localization and camera-derived traversability must be implemented and tested before claiming those features.

---

## 3. Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Host OS** | Windows 11 (64-bit) | WSLg enabled for native hardware-accelerated GUI |
| **Guest OS** | Ubuntu 24.04 LTS (Noble Numbat) | WSL 2 virtualized Linux kernel |
| **Robotics Middleware** | ROS 2 Jazzy Jalisco | Primary Tier-1 LTS release for Ubuntu 24.04 |
| **Physics Simulation** | Gazebo Harmonic (`ros_gz`) | Official simulation suite paired with ROS 2 Jazzy |
| **Navigation** | Nav2 (Navigation 2) | Official ROS 2 Jazzy Nav2 stack |
| **Visualization** | RViz 2 & Gazebo Sim GUI | Hardware-accelerated via DirectX/Mesa in WSLg |
| **Vision / AI** | Python, OpenCV, lightweight pretrained model | TBD by Vision/AI lead |
| **Localization** | SLAM Toolbox (baseline) + Visual SLAM (stretch) | TBD by Localization lead |
| **Version Control** | Git & GitHub | Single repository, feature-branch workflow |

---

## 4. Repository Structure — Every File and Folder

The full file tree below links directly to every file. Click any entry to open it.

```text
trishul-ugv/                        ← repository root
├── README.md                       ← YOU ARE HERE — master entry point
├── .gitignore                      ← excludes build/, install/, logs, models, venvs
├── CONTRIBUTING.md                 ← full Git workflow, ownership, PR, and data rules
├── LICENSE                         ← Apache 2.0
│
├── docs/                           ← all documentation
│   ├── ARCHITECTURE_OVERVIEW.md    ← system diagram & per-module boundaries
│   ├── ENVIRONMENT_SETUP_GUIDE.md  ← step-by-step WSL 2 + ROS 2 + Gazebo setup
│   ├── INTERFACE_PLANNING_CHECKLIST.md ← REP-103/105, sensor & Nav2 checklist
│   └── trishul-ugv-docs/           ← original team reference documentation
│       ├── README.md               ← reading guide for trishul-ugv-docs/
│       ├── PRODUCT.md              ← hackathon context, aims, scope, success measures
│       ├── TEAM_ROLES.md           ← per-member roles, deliverables, and done criteria
│       ├── SETUP_GUIDE.md          ← hardware targets, WSL 2, ROS 2 install, Git setup
│       ├── GIT_WORKFLOW.md         ← branches, commits, PRs, conflict rules
│       ├── INTERFACES.md           ← interface agreement table (fill before coding)
│       ├── TESTING_AND_DEMO.md     ← test layers, scenarios, results table, demo plan
│       ├── AI_CODING_GUIDE.md      ← rules for using AI coding assistants
│       ├── CONTRIBUTING.md         ← quick contributing reference card
│       └── .gitignore              ← ignores within trishul-ugv-docs
│
├── src/                            ← ROS 2 colcon workspace source root
│   ├── trishul_description/        ← URDF/Xacro, meshes, joint kinematics
│   │   └── README.md
│   ├── trishul_simulation/         ← Gazebo worlds, ros_gz_bridge configs
│   │   └── README.md
│   ├── trishul_perception/         ← camera pipeline, AI detection, traversability
│   │   └── README.md
│   ├── trishul_localization/       ← EKF fusion, visual SLAM, TF broadcasting
│   │   └── README.md
│   ├── trishul_navigation/         ← Nav2 params, costmaps, planners, controllers
│   │   └── README.md
│   └── trishul_bringup/            ← master launch files, RViz profiles
│       └── README.md
│
├── tests/                          ← integration tests, launch_testing harnesses
│   └── README.md
│
├── scripts/                        ← developer onboarding and utility scripts
│   ├── setup_workspace.sh          ← verifies Ubuntu 24.04, ROS 2 Jazzy, colcon
│   └── README.md
│
├── results/                        ← test logs, benchmarks, demo screenshots
│   └── README.md
│
└── requirements/                   ← Python dependency declarations
    ├── requirements.txt
    └── README.md
```

### Clickable File Index

**Root**
| File | Purpose |
| :--- | :--- |
| [README.md](README.md) | Master entry point — this file |
| [.gitignore](.gitignore) | Excludes build artifacts, model weights, bags, venvs |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Git branching, commits, PR process, data hygiene |
| [LICENSE](LICENSE) | Apache 2.0 |

**`docs/` — Architectural & Technical Reference**
| File | Purpose |
| :--- | :--- |
| [docs/ARCHITECTURE_OVERVIEW.md](docs/ARCHITECTURE_OVERVIEW.md) | System architecture diagram and module data-flow boundaries |
| [docs/ENVIRONMENT_SETUP_GUIDE.md](docs/ENVIRONMENT_SETUP_GUIDE.md) | Detailed WSL 2 + Ubuntu 24.04 + ROS 2 Jazzy + Gazebo Harmonic setup |
| [docs/INTERFACE_PLANNING_CHECKLIST.md](docs/INTERFACE_PLANNING_CHECKLIST.md) | REP-103/105 frames, sensor bridges, Nav2 & Bringup checklists |

**`docs/trishul-ugv-docs/` — Team Reference Docs** *(read first)*
| File | Purpose |
| :--- | :--- |
| [docs/trishul-ugv-docs/README.md](docs/trishul-ugv-docs/README.md) | Reading guide and technology list |
| [docs/trishul-ugv-docs/PRODUCT.md](docs/trishul-ugv-docs/PRODUCT.md) | Project spec, hackathon context, aims, scope, success measures |
| [docs/trishul-ugv-docs/TEAM_ROLES.md](docs/trishul-ugv-docs/TEAM_ROLES.md) | Per-member roles, deliverables, "done when" criteria |
| [docs/trishul-ugv-docs/SETUP_GUIDE.md](docs/trishul-ugv-docs/SETUP_GUIDE.md) | Hardware targets, WSL 2, ROS 2 install, workspace build |
| [docs/trishul-ugv-docs/GIT_WORKFLOW.md](docs/trishul-ugv-docs/GIT_WORKFLOW.md) | Branching, commits, PRs, conflict rules, what not to commit |
| [docs/trishul-ugv-docs/INTERFACES.md](docs/trishul-ugv-docs/INTERFACES.md) | Interface agreement table — fill in before connecting modules |
| [docs/trishul-ugv-docs/TESTING_AND_DEMO.md](docs/trishul-ugv-docs/TESTING_AND_DEMO.md) | Test layers A–E, scenario checklists, results table, judging demo plan |
| [docs/trishul-ugv-docs/AI_CODING_GUIDE.md](docs/trishul-ugv-docs/AI_CODING_GUIDE.md) | Rules for using Antigravity or any AI coding assistant |
| [docs/trishul-ugv-docs/CONTRIBUTING.md](docs/trishul-ugv-docs/CONTRIBUTING.md) | Quick contributing reference card |

**`src/` — ROS 2 Package Placeholders** *(initialize with `ros2 pkg create`)*
| Directory | Owner | README |
| :--- | :--- | :--- |
| `src/trishul_description/` | Simulation Lead | [README.md](src/trishul_description/README.md) |
| `src/trishul_simulation/` | Simulation Lead | [README.md](src/trishul_simulation/README.md) |
| `src/trishul_perception/` | Vision / AI Lead | [README.md](src/trishul_perception/README.md) |
| `src/trishul_localization/` | Localization Lead | [README.md](src/trishul_localization/README.md) |
| `src/trishul_navigation/` | Navigation Lead | [README.md](src/trishul_navigation/README.md) |
| `src/trishul_bringup/` | Integration Lead | [README.md](src/trishul_bringup/README.md) |

**Supporting Directories**
| File / Directory | Purpose |
| :--- | :--- |
| [tests/README.md](tests/README.md) | QA strategy, linting, `launch_testing` harness guide |
| [scripts/setup_workspace.sh](scripts/setup_workspace.sh) | Bash script — verifies OS, ROS 2, Gazebo, colcon inside WSL 2 |
| [scripts/README.md](scripts/README.md) | How to run the scripts |
| [results/README.md](results/README.md) | What to commit vs. exclude from results/ |
| [requirements/requirements.txt](requirements/requirements.txt) | Python dependency list with Ubuntu 24.04 PEP 668 notes |
| [requirements/README.md](requirements/README.md) | Virtual environment guidance for ROS 2 + Python packages |

---

## 5. Team Roles & Ownership

| # | Role | Owner | Owned Directories | Key Deliverable |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Simulation Lead** | TBD | `src/trishul_description/`<br>`src/trishul_simulation/` | Working robot model + outdoor Gazebo world + sensor topics |
| 2 | **Vision / AI Lead** | TBD | `src/trishul_perception/`<br>`requirements/` | Camera processing node + AI detection + traversability output |
| 3 | **Localization Lead** | TBD | `src/trishul_localization/` | State estimation + TF tree + map/pose output |
| 4 | **Navigation Lead** | TBD | `src/trishul_navigation/` | Nav2 costmaps + path planning + obstacle avoidance |
| 5 | **Integration Lead** | TBD | `src/trishul_bringup/`<br>`docs/` · `scripts/` · `tests/` | Master launch + RViz profile + clean-clone demo |

> For full per-member role details, deliverables, and "done when" criteria see [docs/trishul-ugv-docs/TEAM_ROLES.md](docs/trishul-ugv-docs/TEAM_ROLES.md).

---

## 6. Success Measures

Record actual results — do not invent them in advance. From [docs/trishul-ugv-docs/PRODUCT.md](docs/trishul-ugv-docs/PRODUCT.md):

- Number of goal trials attempted and goals reached.
- Number of collisions observed.
- Whether the perception node received camera frames.
- Whether detections were produced in the tested scenes.
- Whether the localization output behaved as expected.
- Whether the full launch worked after a clean clone and build.

Set actual thresholds with the team after the baseline works.

---

## 7. Key Rules (Summary)

| Rule | Detail |
| :--- | :--- |
| **One repo** | Single `trishul-ugv` repository — no separate repos per module. |
| **No direct pushes to `main`** | All changes go through a feature branch and pull request. |
| **Interface agreement first** | Fill in [INTERFACES.md](docs/trishul-ugv-docs/INTERFACES.md) before connecting modules. |
| **No fake results** | Never describe a feature as complete based only on generated or untested code. |
| **Package init via CLI** | Always use `ros2 pkg create` — never hand-craft empty `package.xml` files. |
| **No large files in Git** | Weights (`*.pt`, `*.onnx`), bags (`*.db3`, `*.mcap`), and `build/install/log/` are gitignored. |
| **WSL file hygiene** | Keep the ROS 2 workspace in the Linux filesystem (`~/trishul-ugv`), not under `/mnt/`. |

---

## 8. Next Steps

1. **Environment** — All members complete [docs/trishul-ugv-docs/SETUP_GUIDE.md](docs/trishul-ugv-docs/SETUP_GUIDE.md) and run `scripts/setup_workspace.sh` to verify.
2. **Git init** — Integration lead initializes the GitHub repository and adds all members.
3. **Interface sign-off** — Team fills in [docs/trishul-ugv-docs/INTERFACES.md](docs/trishul-ugv-docs/INTERFACES.md) during the first architecture meeting.
4. **Phase 1 Milestone** — Simulation lead brings up a minimal robot in Gazebo Harmonic with a camera sensor; Integration lead creates `trishul_bringup` to visualize it in RViz 2.
5. **Phase 2 onward** — Module leads initialize their ROS 2 packages using `ros2 pkg create` and develop in feature branches.

---

## 9. Official Learning References

| Resource | URL |
| :--- | :--- |
| ROS 2 Jazzy Installation | https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html |
| ROS 2 Jazzy Tutorials | https://docs.ros.org/en/jazzy/Tutorials.html |
| Nav2 Documentation | https://docs.nav2.org/ |
| Gazebo Harmonic Docs | https://gazebosim.org/docs/harmonic/ |
| GitHub Docs | https://docs.github.com/en |
