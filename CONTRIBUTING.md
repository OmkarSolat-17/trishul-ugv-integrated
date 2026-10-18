# Contributing to Trishul UGV

Welcome to the Trishul UGV engineering team! This guide establishes our team workflow, Git conventions, code quality expectations, and package ownership boundaries. Adhering to these guidelines ensures smooth integration and reproducible builds.

---

## 1. Team Roles & Folder Ownership Matrix

Each member has primary ownership over specific directories and responsibilities. Cross-boundary changes require review and approval from the affected lead and the Integration Lead.

| Role | Primary Lead | Owned Directories | Key Responsibilities |
| :--- | :--- | :--- | :--- |
| **Simulation Lead** | Simulation Lead | `src/trishul_description/`<br>`src/trishul_simulation/` | Robot physical description (URDF/Xacro), collision/visual geometries, Gazebo Harmonic worlds, sensors simulation, `ros_gz_bridge`. |
| **Vision / AI Lead** | Vision/AI Lead | `src/trishul_perception/`<br>`requirements/` | Camera processing pipeline, AI-based hazard/obstacle detection, perception confidence, traversability feeds. |
| **Localization Lead** | Localization Lead | `src/trishul_localization/` | State estimation, odometry fusion (EKF), visual SLAM/odometry investigation, coordinate frame transforms (`map` -> `odom`). |
| **Navigation Lead** | Navigation Lead | `src/trishul_navigation/` | Nav2 integration, global/local costmap parameterization, path planning, obstacle avoidance controllers, recovery behaviors. |
| **Integration Lead** | Integration Lead | `src/trishul_bringup/`<br>`docs/`<br>`scripts/`<br>`tests/`<br>`results/`<br>Root files (`README.md`, etc.) | System bringup launch files, RViz 2 profiles, cross-module integration testing, Git workflow oversight, demonstration reproducibility. |

---

## 2. Git Workflow & Branching Strategy

We follow a structured Git feature-branch workflow. **Direct commits to `main` are strictly prohibited.**

```
main (protected, stable, verified releases only)
  ▲
  │ Pull Request (Review & CI validation)
  │
feature/<role>-<short-description>
```

### Branch Naming Convention
- `feature/<role>-<feature-name>` (e.g., `feature/sim-urdf-base`, `feature/vision-yolo-detector`)
- `fix/<role>-<issue-description>` (e.g., `fix/nav-costmap-inflation`)
- `docs/<topic>` (e.g., `docs/setup-instructions`)
- `integration/<milestone>` (e.g., `integration/sprint-1-gazebo-bringup`)

### Commit Message Guidelines
We follow the [Conventional Commits](https://www.conventionalcommits.org/) standard:
```
<type>(<scope>): <short description in present tense>

[optional body with details]
```
**Types:**
- `feat`: A new feature or capability.
- `fix`: A bug fix.
- `docs`: Documentation updates only.
- `style`: Formatting, whitespace (no functional code change).
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `test`: Adding or updating test cases.
- `chore`: Build scripts, dependencies, configuration.

**Examples:**
- `feat(sim): add differential drive chassis collision mesh`
- `fix(nav): correct local costmap footprint dimensions`
- `docs(interface): document visual odometry topic checklist`

---

## 3. Pull Request (PR) & Review Process

1. **Keep PRs Small & Focused**: A PR should implement one logical capability or fix. Avoid massive multi-package changes.
2. **Local Pre-Check**:
   - The workspace must build cleanly with zero errors: `colcon build --symlink-install`.
   - Workspace tests and linters must pass: `colcon test`.
3. **Open PR Against `main`**:
   - Provide a clear description of changes.
   - List the testing performed in simulation or unit tests.
   - Attach RViz/Gazebo screenshots if applicable.
4. **Code Review**:
   - At least **one peer review** from another lead is required.
   - Final approval and merge is performed by the **Integration Lead**.

---

## 4. Package Initialization Standards

⚠️ **Crucial Rule for Beginners**:
Never manually create ad-hoc folders and empty `package.xml` files inside `src/`. ROS 2 packages must be initialized using the standard ROS 2 command line tool inside the workspace root:

```bash
# For Python-based ROS 2 packages:
ros2 pkg create --build-type ament_python <package_name> --dependencies rclpy ...

# For C++-based ROS 2 packages:
ros2 pkg create --build-type ament_cmake <package_name> --dependencies rclcpp ...
```

Ensure each initialized package contains:
- Valid `package.xml` with package name, version, description, maintainer email, and license (`Apache-2.0`).
- Proper dependency declarations (`<depend>`, `<exec_depend>`, etc.).
- `setup.py` / `setup.cfg` (Python) or `CMakeLists.txt` (C++).

---

## 5. Large Files, Datasets & Model Weights Policy

Git is designed for text and source code, not binary dumps:
- ❌ **Do NOT commit**:
  - Neural network weights (`*.pt`, `*.onnx`, `*.engine`, `*.weights`, etc.) exceeding 50 MB.
  - ROS bag files (`*.db3`, `*.mcap`).
  - Large point cloud dumps or raw dataset archives.
  - Build output directories (`build/`, `install/`, `log/`).
- ✅ **Proper handling**:
  - Model weights and datasets must be downloaded via reproducible setup scripts in `scripts/` (e.g., using `wget` or `gdown` pointing to Google Drive, Hugging Face, or GitHub Releases).
  - Check `.gitignore` before committing files to ensure binary artifacts are ignored.
