#!/usr/bin/env python3
"""TRISHUL - Depth to LaserScan Converter"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, LaserScan
from cv_bridge import CvBridge
import numpy as np
import math

class DepthToLaserScanNode(Node):
    def __init__(self):
        super().__init__("depth_to_laserscan")
        self.declare_parameter("min_depth", 0.2)
        self.declare_parameter("max_depth", 15.0)
        self.declare_parameter("num_beams", 360)
        self.declare_parameter("fov_degrees", 60.0)
        self.declare_parameter("scan_height_pct", 0.2)
        self.min_depth = self.get_parameter("min_depth").value
        self.max_depth = self.get_parameter("max_depth").value
        self.num_beams = self.get_parameter("num_beams").value
        self.fov = math.radians(self.get_parameter("fov_degrees").value)
        self.scan_height_pct = self.get_parameter("scan_height_pct").value
        self.bridge = CvBridge()
        self.depth_sub = self.create_subscription(
            Image, "/camera/depth/image_raw", self.depth_callback, 10)
        self.scan_pub = self.create_publisher(LaserScan, "/scan", 10)
        self.get_logger().info("Depth->LaserScan READY")

    def depth_callback(self, msg):
        try:
            depth_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="passthrough")
        except Exception as e:
            self.get_logger().error(f"CV Bridge error: {e}")
            return
        h, w = depth_image.shape
        s = int(h * (0.5 - self.scan_height_pct / 2))
        e = int(h * (0.5 + self.scan_height_pct / 2))
        depth_slice = depth_image[s:e, :]
        clean = np.where(depth_slice > 0, depth_slice, self.max_depth)
        min_d = np.min(clean, axis=0)
        cols = np.linspace(0, w - 1, self.num_beams, dtype=int)
        ranges = np.clip(min_d[cols].astype(float), self.min_depth, self.max_depth)
        ranges = np.nan_to_num(ranges, nan=self.max_depth, posinf=self.max_depth)
        scan = LaserScan()
        scan.header.stamp = msg.header.stamp
        scan.header.frame_id = "camera_link"
        scan.angle_min = -self.fov / 2.0
        scan.angle_max = self.fov / 2.0
        scan.angle_increment = self.fov / (self.num_beams - 1)
        scan.time_increment = 0.0
        scan.scan_time = 0.1
        scan.range_min = self.min_depth
        scan.range_max = self.max_depth
        scan.ranges = ranges.tolist()
        scan.intensities = []
        self.scan_pub.publish(scan)

def main(args=None):
    rclpy.init(args=args)
    node = DepthToLaserScanNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
