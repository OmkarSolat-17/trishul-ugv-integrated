#!/usr/bin/env bash
# ==============================================================================
# TRISHUL UGV -- Unified Safe Launcher with WSL2 Headless / Xvfb Auto-Fallback
# ==============================================================================

set -e

PROFILE=""
RENDER_PREF="${TRISHUL_RENDER_MODE:-auto}"  # auto | headless | xvfb | gui
PASSTHROUGH_ARGS=()
HAS_HEADLESS_ARG=0
HAS_RVIZ_ARG=0

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
        --headless)
            RENDER_PREF="headless"
            shift
            ;;
        --xvfb|--software-gl)
            RENDER_PREF="xvfb"
            shift
            ;;
        --gui)
            RENDER_PREF="gui"
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_demo.sh [--profile default|city_normal_4wd|trishul_final_4wd] [--headless|--xvfb|--gui] [ros2 launch args...]"
            exit 0
            ;;
        headless:=*)
            HAS_HEADLESS_ARG=1
            VAL="${1#*=}"
            if [[ "${VAL,,}" == "true" || "$VAL" == "1" ]]; then
                RENDER_PREF="headless"
            fi
            PASSTHROUGH_ARGS+=("$1")
            shift
            ;;
        use_rviz:=*)
            HAS_RVIZ_ARG=1
            PASSTHROUGH_ARGS+=("$1")
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
echo "[TRISHUL] Purging any lingering background Gazebo, Nav2, SLAM, or Dashboard processes..."
for proc in gz ruby parameter_bridge dashboard_server system_coordinator image_processor \
            sensor_monitor status_node async_slam_toolbox_node bt_navigator controller_server \
            planner_server behavior_server smoother_server velocity_smoother collision_monitor \
            waypoint_follower route_server docking_server amcl map_server \
            lifecycle_manager static_transform_publisher rviz2 Xvfb; do
    killall -9 "$proc" 2>/dev/null || true
done
sleep 0.5

echo "[TRISHUL] Sourcing ROS 2 Jazzy and Trishul workspace..."
if [ ! -f "/opt/ros/jazzy/setup.bash" ]; then
    echo "[TRISHUL] Error: /opt/ros/jazzy/setup.bash not found. Install ROS 2 Jazzy first."
    exit 1
fi
source /opt/ros/jazzy/setup.bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export TRISHUL_WORKSPACE="$SCRIPT_DIR"

if [ ! -f "$SCRIPT_DIR/install/setup.bash" ]; then
    echo "[TRISHUL] Workspace not built yet. Running 'colcon build --symlink-install'..."
    (cd "$SCRIPT_DIR" && colcon build --symlink-install)
fi
source "$SCRIPT_DIR/install/setup.bash"

# Export resource paths for Gazebo Harmonic models and worlds
export GZ_SIM_RESOURCE_PATH="$SCRIPT_DIR/models:$SCRIPT_DIR/worlds:${GZ_SIM_RESOURCE_PATH:-}"
export SDF_PATH="$SCRIPT_DIR/models:$SCRIPT_DIR/worlds:${SDF_PATH:-}"

# ==============================================================================
# Graphics & OpenGL 3.3+ Capability Detection (WSL2 D3D12 vs Headless Xvfb)
# Prevents Gazebo Harmonic Ogre2 SIGSEGV (exit 139) when WSL2 lacks HW OpenGL 3.3
# ==============================================================================
USE_XVFB=0
HEADLESS_LAUNCH="False"
USE_RVIZ_LAUNCH="True"

has_nvidia_wsl_gpu() {
    if [ -x "/usr/lib/wsl/lib/nvidia-smi" ] && /usr/lib/wsl/lib/nvidia-smi -L >/dev/null 2>&1; then
        return 0
    fi
    if command -v nvidia-smi >/dev/null 2>&1 && nvidia-smi -L >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

probe_hw_opengl_33() {
    # Requires an active X11/WSLg DISPLAY and glxinfo utility
    if [ -z "${DISPLAY:-}" ] || ! command -v glxinfo >/dev/null 2>&1; then
        return 1
    fi

    local glx_out=""
    if [ -e "/dev/dxg" ]; then
        if has_nvidia_wsl_gpu; then
            glx_out="$(GALLIUM_DRIVER=d3d12 MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA LIBGL_ALWAYS_SOFTWARE=0 glxinfo -B 2>&1 || true)"
        else
            glx_out="$(GALLIUM_DRIVER=d3d12 LIBGL_ALWAYS_SOFTWARE=0 glxinfo -B 2>&1 || true)"
        fi
    else
        glx_out="$(LIBGL_ALWAYS_SOFTWARE=0 glxinfo -B 2>&1 || true)"
    fi

    # Reject if drisw/GLX failed or hardware acceleration is unavailable
    if echo "$glx_out" | grep -qiE "failed to create|error|unable to open display|Accelerated: no|llvmpipe|softpipe"; then
        return 1
    fi

    # Extract OpenGL core profile major.minor version and verify >= 3.3
    local ver
    ver="$(echo "$glx_out" | sed -n 's/.*OpenGL core profile version string: *\([0-9]\+\.[0-9]\+\).*/\1/p' | head -n 1)"
    if [ -z "$ver" ]; then
        ver="$(echo "$glx_out" | sed -n 's/.*OpenGL version string: *\([0-9]\+\.[0-9]\+\).*/\1/p' | head -n 1)"
    fi
    if [ -z "$ver" ]; then
        return 1
    fi

    local major="${ver%%.*}"
    local minor="${ver#*.}"
    minor="${minor%%[^0-9]*}"
    if [ "${major:-0}" -gt 3 ] || { [ "${major:-0}" -eq 3 ] && [ "${minor:-0}" -ge 3 ]; }; then
        return 0
    fi
    return 1
}

if [[ "$RENDER_PREF" == "headless" || "$RENDER_PREF" == "xvfb" ]]; then
    echo "[TRISHUL] Render Mode: Headless Virtual Framebuffer + Mesa llvmpipe (explicitly requested)"
    USE_XVFB=1
    HEADLESS_LAUNCH="True"
    USE_RVIZ_LAUNCH="False"
elif [[ "$RENDER_PREF" == "gui" ]] && [ -n "${DISPLAY:-}" ]; then
    echo "[TRISHUL] Render Mode: GUI Mode requested on DISPLAY=${DISPLAY}"
    if probe_hw_opengl_33; then
        USE_XVFB=0
    else
        echo "[TRISHUL] Warning: Hardware OpenGL 3.3+ not verified; enabling software llvmpipe fallback."
        unset MESA_D3D12_DEFAULT_ADAPTER_NAME
        export LIBGL_ALWAYS_SOFTWARE=1
        export GALLIUM_DRIVER=llvmpipe
        export LP_NUM_THREADS="${LP_NUM_THREADS:-4}"
    fi
else
    # Auto-detect hardware OpenGL >= 3.3 vs Headless Xvfb Software Rendering
    if probe_hw_opengl_33; then
        echo "[TRISHUL] Hardware OpenGL 3.3+ acceleration verified! Using GPU-accelerated rendering."
        USE_XVFB=0
        HEADLESS_LAUNCH="False"
        USE_RVIZ_LAUNCH="True"
    else
        echo "[TRISHUL] Hardware OpenGL 3.3+ unavailable on current WSL2/display environment."
        echo "[TRISHUL] Auto-switching Gazebo Harmonic to Headless Server + Xvfb Software Rendering (llvmpipe)."
        USE_XVFB=1
        HEADLESS_LAUNCH="True"
        USE_RVIZ_LAUNCH="False"
    fi
fi

if [ "$USE_XVFB" -eq 1 ]; then
    unset GALLIUM_DRIVER
    unset MESA_D3D12_DEFAULT_ADAPTER_NAME
    export LIBGL_ALWAYS_SOFTWARE=1
    export GALLIUM_DRIVER=llvmpipe
    export LP_NUM_THREADS="${LP_NUM_THREADS:-4}"
    export QT_XCB_GL_INTEGRATION=none

    if ! command -v xvfb-run >/dev/null 2>&1; then
        echo "[TRISHUL] 'xvfb-run' not found. Attempting to install 'xvfb' and 'mesa-utils'..."
        if command -v sudo >/dev/null 2>&1; then
            sudo apt-get update && sudo apt-get install -y xvfb mesa-utils libgl1-mesa-dri || true
        fi
    fi
else
    if [ -z "${LIBGL_ALWAYS_SOFTWARE:-}" ]; then
        if [ -e "/dev/dxg" ]; then
            export GALLIUM_DRIVER=d3d12
            if has_nvidia_wsl_gpu; then
                export MESA_D3D12_DEFAULT_ADAPTER_NAME="NVIDIA"
                export CUDA_VISIBLE_DEVICES=0
            else
                unset MESA_D3D12_DEFAULT_ADAPTER_NAME
            fi
            export LIBGL_ALWAYS_SOFTWARE=0
        fi
    fi
fi

LAUNCH_ARGS=()
if [ "$HAS_HEADLESS_ARG" -eq 0 ]; then
    LAUNCH_ARGS+=("headless:=${HEADLESS_LAUNCH}")
fi
if [ "$HAS_RVIZ_ARG" -eq 0 ]; then
    LAUNCH_ARGS+=("use_rviz:=${USE_RVIZ_LAUNCH}")
fi
LAUNCH_ARGS+=("${PASSTHROUGH_ARGS[@]}")

case "$PROFILE" in
    default)
        TARGET_CMD=(ros2 launch trishul_bringup demo.launch.py "${LAUNCH_ARGS[@]}")
        ;;
    city_normal_4wd)
        TARGET_CMD=(ros2 launch trishul_bringup city_4wd_demo.launch.py world:=city_normal.sdf "${LAUNCH_ARGS[@]}")
        ;;
    trishul_final_4wd)
        TARGET_CMD=(ros2 launch trishul_bringup city_4wd_demo.launch.py world:=trishul_final.sdf "${LAUNCH_ARGS[@]}")
        ;;
esac

echo "[TRISHUL] Launching Trishul UGV Mission Control ($PROFILE)..."
echo "[TRISHUL] Web Dashboard will be available at: http://127.0.0.1:8090"

if [ "$USE_XVFB" -eq 1 ] && command -v xvfb-run >/dev/null 2>&1; then
    export TRISHUL_XVFB_ACTIVE=1
    exec xvfb-run -a -s "-screen 0 1280x1024x24 +extension GLX +render -noreset" "${TARGET_CMD[@]}"
else
    exec "${TARGET_CMD[@]}"
fi
