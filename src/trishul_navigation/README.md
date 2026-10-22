# trishul_navigation

> **Owner**: Navigation Lead  
> **Status**: In Active Development

## Scope & Purpose
This package houses Nav2 configuration, autonomous navigation pipelines, and sensor monitoring nodes for the Trishul UGV:
- `sensor_monitor`: Subscribes to `/scan` (LiDAR) to evaluate proximity danger thresholds (`DANGER` < 0.25m, `WARNING` < 0.50m, `CLEAR`) and angular sectors (`FRONT`, `LEFT`, `RIGHT`, etc.).
- `status_node`: Periodic 1 Hz heartbeat publisher on `trishul/status`.
- Nav2 parameter files and launch pipelines for simulation and autonomous traversal.

## Nodes & Usage

### 1. Build
```bash
colcon build --packages-select trishul_navigation
source install/setup.bash
```

### 2. Run Sensor Monitor
```bash
ros2 run trishul_navigation sensor_monitor
```

### 3. Run Status Node
```bash
ros2 run trishul_navigation status_node
```

## Running Tests
```bash
colcon test --packages-select trishul_navigation
colcon test-result --all
```
