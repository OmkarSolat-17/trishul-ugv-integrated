#!/usr/bin/env bash
# ==============================================================================
# Trishul UGV - Workspace Verification & Setup Helper
# Run this inside Ubuntu 24.04 (WSL 2)
# ==============================================================================

set -e

echo "=== Trishul UGV: Checking Development Environment ==="

# 1. Check OS Distribution
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "[✓] Detected OS: $NAME $VERSION_ID (${UBUNTU_CODENAME:-$VERSION_CODENAME})"
    if [ "${UBUNTU_CODENAME:-}" != "noble" ]; then
        echo "[!] Warning: Target environment is Ubuntu 24.04 LTS (Noble Numbat). Found: ${UBUNTU_CODENAME:-$VERSION_CODENAME}"
    fi
else
    echo "[!] Unknown Linux Distribution."
fi

# 2. Check ROS 2 Jazzy Installation
if [ -z "${ROS_DISTRO:-}" ]; then
    if [ -f "/opt/ros/jazzy/setup.bash" ]; then
        echo "[✓] Sourcing /opt/ros/jazzy/setup.bash..."
        source /opt/ros/jazzy/setup.bash
    else
        echo "[X] ROS 2 Jazzy not found in /opt/ros/jazzy. Please follow docs/ENVIRONMENT_SETUP_GUIDE.md."
        exit 1
    fi
fi

echo "[✓] Active ROS 2 Distribution: $ROS_DISTRO"
if [ "$ROS_DISTRO" != "jazzy" ]; then
    echo "[!] Warning: Expected ROS 2 'jazzy', but found '$ROS_DISTRO'."
fi

# 3. Check Gazebo Sim
if command -v gz &> /dev/null; then
    GZ_VER=$(gz sim --version | head -n 1 || true)
    echo "[✓] Gazebo Sim Installed: $GZ_VER"
else
    echo "[!] Gazebo ('gz') not found. Install via 'sudo apt install ros-jazzy-ros-gz'."
fi

# 4. Check Xvfb & Mesa OpenGL Utilities (Required for WSL2 headless sensor rendering)
if command -v xvfb-run &> /dev/null; then
    echo "[✓] xvfb-run virtual framebuffer is available (WSL2 headless Gazebo fallback ready)."
else
    echo "[!] xvfb-run not found. Install via 'sudo apt install -y xvfb mesa-utils libgl1-mesa-dri'."
fi

if command -v glxinfo &> /dev/null; then
    echo "[✓] glxinfo (mesa-utils) is available."
else
    echo "[!] glxinfo not found. Install via 'sudo apt install -y mesa-utils'."
fi

# 5. Check Colcon & Build Tools
if command -v colcon &> /dev/null; then
    echo "[✓] colcon build tool is available."
else
    echo "[!] colcon not found. Install via 'sudo apt install python3-colcon-common-extensions'."
fi

# 6. Check rosdep
if command -v rosdep &> /dev/null; then
    echo "[✓] rosdep is available."
else
    echo "[!] rosdep not found. Install via 'sudo apt install python3-rosdep'."
fi

echo ""
echo "=== Environment check complete. You are ready to develop in the workspace! ==="
