#!/usr/bin/env bash
# ==============================================================================
# TRISHUL UGV -- Safe Launcher Script with Simulation Profile Selector
# ==============================================================================

set -e

PROFILE=""
PASSTHROUGH_ARGS=()

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile|-p)
            PROFILE="$2"
            shift 2
            ;;
        --profile=*)
            PROFILE="${1#*=}"
            shift
            ;;
        *)
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
    esac
done

# If no profile specified, display interactive menu
if [ -z "$PROFILE" ]; then
    echo "=============================================================="
    echo "       TRISHUL UGV - SIMULATION PROFILE SELECTOR"
    echo "=============================================================="
    echo " 1) default           Standard UGV in TB3 Sandbox (AMCL) [Default]"
    echo " 2) city_normal_4wd   4WD Skid-Steer UGV in City Normal World (SLAM)"
    echo " 3) trishul_final_4wd 4WD Skid-Steer UGV in Final City World (SLAM)"
    echo " 4) exit              Cancel and exit"
    echo "=============================================================="
    read -r -p "Enter choice [1-4] (default: 1): " CHOICE

    case "$CHOICE" in
        1|"")
            PROFILE="default"
            ;;
        2)
            PROFILE="city_normal_4wd"
            ;;
        3)
            PROFILE="trishul_final_4wd"
            ;;
        4|"q"|"quit"|"exit")
            echo "[TRISHUL] Launch cancelled by user."
            exit 0
            ;;
        *)
            echo "[TRISHUL] Invalid selection. Aborting."
            exit 1
            ;;
    esac
fi

# Validate profile
case "$PROFILE" in
    default|city_normal_4wd|trishul_final_4wd)
        ;;
    *)
        echo "[TRISHUL] Error: Unknown profile '$PROFILE'."
        echo "Supported profiles: default, city_normal_4wd, trishul_final_4wd"
        exit 1
        ;;
esac

echo "[TRISHUL] Selected Profile: $PROFILE"
echo "[TRISHUL] Purging any lingering background Gazebo or bridge processes..."
killall -9 gz 2>/dev/null || true
killall -9 ruby 2>/dev/null || true
killall -9 parameter_bridge 2>/dev/null || true

sleep 0.5

echo "[TRISHUL] Sourcing ROS 2 Jazzy and Trishul workspace..."
source /opt/ros/jazzy/setup.bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/install/setup.bash" ]; then
    source "$SCRIPT_DIR/install/setup.bash"
elif [ -f "/home/papa_ji/project/Trishul/merg-trishul/install/setup.bash" ]; then
    source /home/papa_ji/project/Trishul/merg-trishul/install/setup.bash
fi

# Export resource paths for Gazebo Harmonic models and worlds
export GZ_SIM_RESOURCE_PATH="$SCRIPT_DIR/models:$SCRIPT_DIR/worlds:${GZ_SIM_RESOURCE_PATH:-}"
export SDF_PATH="$SCRIPT_DIR/models:$SCRIPT_DIR/worlds:${SDF_PATH:-}"

# ==============================================================================
# GPU Acceleration & Workload Balancing (NVIDIA GeForce RTX 3060 in WSL2)
# Offload Gazebo Harmonic Ogre2, RViz2 OpenGL, and Qt from CPU/iGPU to RTX GPU
# ==============================================================================
# ==============================================================================
# GPU Hardware Acceleration via D3D12 on NVIDIA GeForce RTX 3050 (GPU 1)
# ==============================================================================
export GALLIUM_DRIVER=d3d12
export MESA_D3D12_DEFAULT_ADAPTER_NAME="NVIDIA"
export LIBGL_ALWAYS_SOFTWARE=0
export CUDA_VISIBLE_DEVICES=0

echo "[TRISHUL] Launching Trishul UGV Mission Control ($PROFILE)..."

case "$PROFILE" in
    default)
        exec ros2 launch trishul_bringup demo.launch.py "${PASSTHROUGH_ARGS[@]}"
        ;;
    city_normal_4wd)
        exec ros2 launch trishul_bringup city_4wd_demo.launch.py world:=city_normal.sdf "${PASSTHROUGH_ARGS[@]}"
        ;;
    trishul_final_4wd)
        exec ros2 launch trishul_bringup city_4wd_demo.launch.py world:=trishul_final.sdf "${PASSTHROUGH_ARGS[@]}"
        ;;
esac
