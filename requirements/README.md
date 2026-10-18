# Requirements & Dependencies

> **Owner**: Vision / AI Lead & Integration Lead

This directory documents system packages, Python libraries, and environment requirements.

## Ubuntu 24.04 (Noble) & Python Packaging Note
Ubuntu 24.04 enforces [PEP 668](https://peps.python.org/pep-0668/) ("externally-managed-environment"). This means `pip install` cannot be run globally against the system Python interpreter without a virtual environment or apt packages.

### Recommended Approaches:
1. **For ROS 2 Nodes**: Always prefer standard Ubuntu/ROS packages:
   ```bash
   sudo apt install -y python3-numpy python3-opencv python3-scipy
   ```
2. **For AI Model Training & Offline Inference Testing**:
   Create a Python virtual environment:
   ```bash
   python3 -m venv .venv --system-site-packages
   source .venv/bin/activate
   pip install -r requirements/requirements.txt
   ```
   *(Note: `--system-site-packages` ensures ROS 2 Python packages from `/opt/ros/jazzy` remain accessible inside the virtual environment).*
