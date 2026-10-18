# trishul_perception

> **Owner**: Vision / AI Lead  
> **Status**: ⚠️ Placeholder (Package Not Yet Initialized)

## Scope & Purpose
This package will house camera data processing and AI perception:
- Camera subscriber and preprocessing pipeline (OpenCV / cv_bridge).
- AI object and hazard detection nodes (e.g. YOLO, MobileNet, or custom models).
- Traversability analysis and visual obstacle feed for Nav2 costmaps.
- Visualization markers for detected hazards in RViz 2.

## Future Package Initialization
Depending on whether C++ or Python is chosen for your inference pipeline:
```bash
# Python-based pipeline (recommended for PyTorch/ONNX/OpenCV fast prototyping):
cd <workspace_root>
ros2 pkg create --build-type ament_python trishul_perception --dependencies rclpy sensor_msgs vision_msgs cv_bridge

# Or C++-based pipeline (for high-throughput TensorRT / ONNXRuntime):
ros2 pkg create --build-type ament_cmake trishul_perception --dependencies rclcpp sensor_msgs vision_msgs cv_bridge image_transport
```
*Note: Do not create manual empty `package.xml` or `setup.py` files before running the standard tool.*
