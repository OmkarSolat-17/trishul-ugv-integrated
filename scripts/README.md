# Development & Automation Scripts

> **Owner**: Integration Lead

This directory contains utility scripts to automate environment checks, asset downloads, and workspace setup.

## Available Scripts

- `setup_workspace.sh`: Verifies OS release (Ubuntu 24.04 Noble), ROS 2 distribution (`jazzy`), Gazebo Harmonic, and colcon tooling inside WSL 2.

## Usage
Run directly inside your WSL 2 terminal from the workspace root:
```bash
chmod +x scripts/setup_workspace.sh
./scripts/setup_workspace.sh
```
