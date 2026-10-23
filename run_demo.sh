#!/usr/bin/env bash
# ==============================================================================
# TRISHUL UGV -- Safe Launcher Script
# Automatically cleans any zombie gz sim processes to prevent TF timestamp conflicts
# ==============================================================================

echo "[TRISHUL] Purging any lingering background Gazebo or bridge processes..."
killall -9 gz 2>/dev/null || true
killall -9 ruby 2>/dev/null || true
killall -9 parameter_bridge 2>/dev/null || true

sleep 0.5

echo "[TRISHUL] Sourcing ROS 2 Jazzy and Trishul workspace..."
source /opt/ros/jazzy/setup.bash
source /home/papa_ji/project/Trishul/merg-trishul/install/setup.bash

echo "[TRISHUL] Launching Trishul UGV Mission Control..."
ros2 launch trishul_bringup demo.launch.py "$@"
