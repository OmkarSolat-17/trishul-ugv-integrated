# Setup Guide

This guide is for the Trishul team. Follow it carefully and verify each stage before continuing.

## 1. Before installing

Recommended demo laptop:
- Windows 11, 64-bit
- 16 GB RAM recommended
- SSD with about 100 GB free space recommended for the overall environment
- Compatible graphics driver/OpenGL support
- A modern CPU; the team's Dell G15 with 13th-generation Intel Core i7 HX and RTX 3050 6 GB is a reasonable candidate, but test the actual workload

These are practical targets, not universal minimum requirements. Gazebo and RViz performance depends on graphics, drivers, world complexity and WSL configuration.

## 2. Install WSL 2 and Ubuntu

On Windows, open PowerShell as Administrator and run:

```powershell
wsl --install -d Ubuntu-24.04
```

Restart Windows if requested. Open Ubuntu from the Start menu and finish the first-time username/password setup.

Check WSL versions from PowerShell:

```powershell
wsl --list --verbose
```

Ubuntu should use WSL 2. Follow Microsoft's current WSL documentation if installation differs on your machine.

## 3. Update Ubuntu

In the Ubuntu terminal:

```bash
sudo apt update
sudo apt upgrade -y
```

## 4. Install ROS 2 Jazzy

Follow the official instructions exactly:
https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html

Do not rely only on an old copied command list. The official guide includes repository setup, keys, package selection and environment setup.

After installation, use the official ROS 2 tutorial to verify the environment before adding Gazebo, Nav2 or AI dependencies.

## 5. Install the required project stack

After confirming the ROS 2 installation and compatibility, the team will install the packages required for the chosen baseline:
- ROS 2 Jazzy and build tools
- Compatible Gazebo Harmonic ROS integration
- Nav2
- RViz 2
- SLAM Toolbox if the range-sensor baseline is selected
- Camera bridge and `cv_bridge` packages if needed
- Python/OpenCV and the chosen AI model dependencies

Use official documentation and the team's tested dependency list. Do not install every advanced package on every laptop unless that member needs it.

## 6. Git setup

Install Git if it is not available, then configure identity:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-email@example.com"
```

Use the email configured for your GitHub account if you want commits linked to it. Never share passwords or access tokens in the repository.

## 7. Clone the repository

Once the owner has created the GitHub repository:

```bash
cd ~
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd trishul-ugv
```

Replace the placeholder with the real repository URL.

## 8. ROS 2 workspace build

When valid ROS 2 packages have been added under `src/`, build from the repository root:

```bash
source /opt/ros/jazzy/setup.bash
rosdep update
rosdep install --from-paths src --ignore-src -r -y
colcon build
source install/setup.bash
```

If `src/` contains only placeholders and no valid packages, the workspace is not ready for a meaningful build yet. Do not claim success until the command has been run and checked.

## 9. Storage and files

- WSL Linux files usually live inside the WSL virtual disk.
- Windows drives are accessible inside Ubuntu under `/mnt/c/`, `/mnt/d/`, and so on if those drives exist.
- Keep the active ROS 2 workspace in the Linux filesystem, for example `~/trishul-ugv`, for a good development workflow.
- Keep about 100 GB free if possible for packages, build outputs, models, assets and recordings. The repository itself does not need 100 GB.
- Do not commit `build/`, `install/`, `log/`, Python caches, local secrets or huge generated files.

## 10. Official references

- ROS 2 Jazzy installation: https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html
- ROS 2 Jazzy tutorials: https://docs.ros.org/en/jazzy/Tutorials.html
- Nav2: https://docs.nav2.org/
- Gazebo Harmonic: https://gazebosim.org/docs/harmonic/

## Troubleshooting rule

If a command fails:
1. Copy the full error message.
2. Record the Ubuntu version, ROS distribution and command used.
3. Search the official documentation.
4. Ask for help with the exact error.
5. Do not randomly mix instructions for different ROS distributions.
