# Environment Setup Guide: Windows 11 + WSL 2 + ROS 2 Jazzy + Gazebo Harmonic

This document guides the team through setting up a clean, reproducible development environment on a Windows 11 laptop using WSL 2 and Ubuntu 24.04 LTS.

---

## 1. System Architecture & Compatibility Confirmation

| Component | Target Version | Compatibility Note |
| :--- | :--- | :--- |
| **Host OS** | Windows 11 (Build 22000+) | Built-in WSLg support for native GUI acceleration (DirectX vGPU). |
| **Virtualization** | WSL 2 | Default WSL version on Windows 11. Run `wsl --version` to verify. |
| **Linux Distribution** | Ubuntu 24.04 LTS (Noble Numbat) | Tier-1 supported platform for ROS 2 Jazzy Jalisco. |
| **ROS 2 Distribution** | ROS 2 Jazzy Jalisco | LTS release (May 2024 - May 2029). Standard on Ubuntu 24.04. |
| **Gazebo Simulator** | Gazebo Harmonic (Gz Harmonic) | The official default simulation paired with ROS 2 Jazzy (`ros-jazzy-ros-gz`). |
| **Build System** | `colcon` with `ament_cmake` & `ament_python` | Standard ROS 2 workspace tooling. |

> **Why this stack?**
> ROS 2 Jazzy paired with Gazebo Harmonic provides official upstream support, eliminates legacy Gazebo Classic (`gazebo-11`) deprecation issues, and works seamlessly with Nav2 and ROS 2 Jazzy binaries on Ubuntu 24.04.

---

## 2. Windows 11 Host Preparation

### Step 2.1: Verify or Install WSL 2 with Ubuntu 24.04
In Windows PowerShell (Run as Administrator):
```powershell
# Update WSL to the latest release
wsl --update

# List available distributions
wsl --list --online

# Install Ubuntu 24.04 LTS
wsl --install -d Ubuntu-24.04
```

### Step 2.2: Ensure Graphics Drivers are Up-to-Date
WSLg utilizes vGPU acceleration through your Windows graphics driver:
- **NVIDIA GPU**: Install latest GeForce Game Ready or Studio Driver on Windows.
- **AMD / Intel GPU**: Install latest Windows display drivers.
*(No Linux graphics driver needs to be manually installed inside WSL).*

---

## 3. Ubuntu 24.04 Configuration (Inside WSL 2)

Open your Ubuntu 24.04 terminal:

### Step 3.1: System Updates & Essential Tools
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y locales curl gnupg lsb-release build-essential git python3-pip python3-venv mesa-utils
```

### Step 3.2: Verify 3D Acceleration in WSLg
Check that OpenGL acceleration is functioning:
```bash
glxinfo -B
```
You should see `Device: D3D12 (NVIDIA / AMD / Intel)` and `Accelerated: yes`.

---

## 4. Install ROS 2 Jazzy Jalisco

Follow the official ROS 2 Jazzy binary installation:

```bash
# 1. Set locale
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8

# 2. Add the ROS 2 repository key
sudo apt install -y software-properties-common
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# 3. Add ROS 2 apt repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# 4. Install ROS 2 Desktop (includes RViz 2 and core demos)
sudo apt update
sudo apt install -y ros-jazzy-desktop

# 5. Install development tools and rosdep
sudo apt install -y python3-colcon-common-extensions python3-rosdep
sudo rosdep init
rosdep update
```

---

## 5. Install Gazebo Harmonic & ROS-Gazebo Bridge

```bash
# Install Gazebo Harmonic and the ROS 2 Jazzy bridge
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-ros-gz-sim ros-jazzy-ros-gz-bridge ros-jazzy-ros-gz-image

# Optional: verify Gazebo standalone launch
gz sim -v 4 -s
```

---

## 6. Install Navigation & Perception Dependencies (When Ready)

```bash
# Navigation 2 (Nav2) for ROS 2 Jazzy
sudo apt install -y ros-jazzy-navigation2 ros-jazzy-nav2-bringup

# Transform (TF2) and vision tools
sudo apt install -y ros-jazzy-tf2-tools ros-jazzy-vision-msgs ros-jazzy-image-transport
```

---

## 7. Environment Auto-Sourcing

Add ROS 2 environment sourcing to your `~/.bashrc`:
```bash
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

Verify your setup:
```bash
echo $ROS_DISTRO
# Output should be: jazzy
```
