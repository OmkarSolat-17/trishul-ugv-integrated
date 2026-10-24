#!/usr/bin/env python3
"""
TRISHUL UGV -- Vision-AI & YOLO Tactical Decision-Making Engine
1. Real-time Object Detection with YOLO (or Tactical CV Depth-Saliency Fallback).
2. 3D Spatial Metric Extraction (Distance Z, Lateral Offset X) using RealSense Depth.
3. Active Route Decision-Making:
   - Critical Proximity (<1.8m in path) -> Active Vision Emergency Stop.
   - Yield Zone (1.8m - 6.0m in path) -> Dynamic Speed Limit Throttling for Safe Passage.
   - Clear Corridor -> Dynamic Speed Restoration.
4. PointCloud2 Vision Obstacle Projection to Nav2 Costmap for Automated Rerouting.
5. Real-time Tactical HUD Video Stream & Decision Telemetry to Dashboard.
"""

import json
import math
import os
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from cv_bridge import CvBridge

from geometry_msgs.msg import Twist
from sensor_msgs.msg import Image, PointCloud2
from std_msgs.msg import String, Header

try:
    import sensor_msgs_py.point_cloud2 as pc2
    PC2_AVAILABLE = True
except ImportError:
    PC2_AVAILABLE = False

try:
    from nav2_msgs.msg import SpeedLimit
    NAV2_SPEED_LIMIT_AVAILABLE = True
except ImportError:
    NAV2_SPEED_LIMIT_AVAILABLE = False

try:
    from ultralytics import YOLO
    import torch
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from ament_index_python.packages import get_package_share_directory


class ImageProcessor(Node):
    def __init__(self):
        super().__init__('image_processor')

        pkg_dir = get_package_share_directory('trishul_perception')
        best_model = os.path.join(pkg_dir, 'models', 'best.pt')
        default_model = best_model if os.path.exists(best_model) else os.path.join(pkg_dir, 'models', 'yolo26n.pt')

        # Declare parameters
        self.declare_parameter('model_path', default_model)
        self.declare_parameter('confidence', 0.35)
        self.declare_parameter('color_topic', '/camera/color/image_raw')
        self.declare_parameter('depth_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/ugv/combined/image')
        self.declare_parameter('detections_topic', '/ugv/detections')
        self.declare_parameter('decision_topic', '/ugv/yolo_decision')
        self.declare_parameter('vision_obstacles_topic', '/ugv/vision_obstacles')
        self.declare_parameter('target_cruise_speed', 2.5)

        self.model_path = self.get_parameter('model_path').value
        self.confidence = float(self.get_parameter('confidence').value)
        color_topic = self.get_parameter('color_topic').value
        depth_topic = self.get_parameter('depth_topic').value
        output_topic = self.get_parameter('output_topic').value
        detections_topic = self.get_parameter('detections_topic').value
        decision_topic = self.get_parameter('decision_topic').value
        vision_obstacles_topic = self.get_parameter('vision_obstacles_topic').value

        self.bridge = CvBridge()
        self.model = None
        self.latest_depth_img = None
        self.latest_depth_time = 0.0
        self.last_decision_state = 'CLEAR'
        self.last_speed_limit_published = 2.5
        self.last_speed_pub_time = 0.0

        # Load YOLO Model if available
        if ULTRALYTICS_AVAILABLE:
            if os.path.exists(self.model_path):
                self.device = 0 if torch.cuda.is_available() else 'cpu'
                self.get_logger().info(f'[VISION-AI] Initializing YOLO from {self.model_path} on device {self.device}')
                try:
                    self.model = YOLO(self.model_path)
                    self.get_logger().info('[VISION-AI] YOLO Deep Neural Network loaded successfully.')
                except Exception as ex:
                    self.get_logger().error(f'[VISION-AI] Failed to load YOLO: {ex}. Using Tactical CV Engine.')
            else:
                self.get_logger().warn(f'[VISION-AI] Model weights not found at {self.model_path}. Using Tactical CV Engine.')
        else:
            self.get_logger().info('[VISION-AI] High-Speed Tactical Computer Vision Engine Active.')

        qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=5
        )

        # Subscriptions
        self.color_sub = self.create_subscription(
            Image, color_topic, self.color_callback, qos
        )
        self.depth_sub = self.create_subscription(
            Image, depth_topic, self.depth_callback, qos
        )

        # Publishers
        self.depth_heatmap_pub = self.create_publisher(Image, '/ugv/depth/heatmap', 5)
        self.image_pub = self.create_publisher(Image, output_topic, 5)
        self.det_pub = self.create_publisher(String, detections_topic, 10)
        self.decision_pub = self.create_publisher(String, decision_topic, 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.vision_obstacles_pub = self.create_publisher(PointCloud2, vision_obstacles_topic, 10)

        if NAV2_SPEED_LIMIT_AVAILABLE:
            self.speed_limit_pub = self.create_publisher(SpeedLimit, '/speed_limit', 10)

        self.get_logger().info(
            f'[VISION-AI] Trishul Tactical Perception & Decision Engine Online.\n'
            f'   Color: {color_topic} | Depth: {depth_topic} -> Out: {output_topic}\n'
            f'   Decisions: {decision_topic} | Costmap Obstacles: {vision_obstacles_topic}'
        )

    def depth_callback(self, msg):
        """Cache floating-point depth image for 3D metric spatial reasoning."""
        try:
            if msg.encoding in ('32FC1', '16UC1'):
                depth_cv = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                if msg.encoding == '16UC1':
                    depth_cv = depth_cv.astype(np.float32) / 1000.0
                self.latest_depth_img = np.nan_to_num(depth_cv, nan=10.0, posinf=10.0, neginf=0.0)
                self.latest_depth_time = time.time()
                depth_scaled = np.clip(self.latest_depth_img / 6.0 * 255.0, 0, 255).astype(np.uint8)
                heatmap = cv2.applyColorMap(depth_scaled, cv2.COLORMAP_TURBO)
                hm_msg = self.bridge.cv2_to_imgmsg(heatmap, encoding='bgr8')
                hm_msg.header = msg.header
                self.depth_heatmap_pub.publish(hm_msg)
        except Exception as e:
            self.get_logger().error(f'Depth processing error: {e}', throttle_duration_sec=3.0)

    def color_callback(self, msg):
        """Processes RGB frame with YOLO, fuses with depth, makes decisions, and injects costmap obstacles."""
        try:
            color_frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            h, w = color_frame.shape[:2]

            detections_list = []
            obstacle_points = []
            critical_threats = []
            yield_threats = []

            # 1. Object Detection (YOLO or Tactical CV Engine)
            if self.model is not None:
                results = self.model.predict(
                    source=color_frame,
                    imgsz=640,
                    conf=self.confidence,
                    device=self.device,
                    verbose=False
                )
                boxes = results[0].boxes
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    name = self.model.names.get(class_id, f'obj_{class_id}')
                    xyxy = box.xyxy[0].cpu().numpy()
                    x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                    detections_list.append({
                        'class': name,
                        'confidence': round(conf, 3),
                        'bbox': [x1, y1, x2, y2]
                    })
            else:
                detections_list = self._tactical_cv_detect(color_frame)

            # 2. 3D Spatial Fusion & Threat Calculation
            has_depth = (self.latest_depth_img is not None and (time.time() - self.latest_depth_time) < 1.0)

            for det in detections_list:
                x1, y1, x2, y2 = det['bbox']
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                bw = max(1, x2 - x1)
                bh = max(1, y2 - y1)

                dist_m = 10.0
                if has_depth and 0 <= cy < h and 0 <= cx < w:
                    y_min, y_max = max(0, cy - 3), min(h, cy + 4)
                    x_min, x_max = max(0, cx - 3), min(w, cx + 4)
                    depth_patch = self.latest_depth_img[y_min:y_max, x_min:x_max]
                    valid_depths = depth_patch[depth_patch > 0.1]
                    if len(valid_depths) > 0:
                        dist_m = float(np.median(valid_depths))
                    else:
                        dist_m = float(self.latest_depth_img[cy, cx])
                else:
                    dist_m = float(np.clip(320.0 / max(bh, 15), 0.5, 10.0))

                dist_m = float(np.clip(dist_m, 0.2, 12.0))
                det['distance'] = round(dist_m, 2)

                metric_x = (cx - (w / 2.0)) * (dist_m / 554.25)
                metric_y = (cy - (h / 2.0)) * (dist_m / 554.25)
                metric_z = dist_m
                det['lateral_x'] = round(metric_x, 2)

                # Generate 3D point cluster for Nav2 Costmap
                if 0.3 < dist_m < 9.0:
                    for dx in np.linspace(-0.25, 0.25, 3):
                        for dz in np.linspace(-0.20, 0.20, 3):
                            obstacle_points.append([float(metric_z + dz), float(-metric_x + dx), 0.1])

                # Check if obstacle is directly inside the vehicle driving corridor (|metric_x| <= 1.25m)
                if abs(metric_x) <= 1.25 and dist_m > 0.3:
                    if dist_m < 2.0:
                        critical_threats.append(det)
                    elif dist_m < 6.0:
                        yield_threats.append(det)

            # 3. Tactical Route Decision-Making
            decision_msg = {
                'timestamp': time.time(),
                'action': 'CLEAR',
                'speed_limit': 2.5,
                'target': 'NONE',
                'distance': 10.0,
                'reason': 'Corridor clear'
            }

            hud_color = (0, 255, 0)
            hud_text = "AI DECISION: PATH CLEAR [CRUISE MODE]"

            if critical_threats:
                closest = min(critical_threats, key=lambda d: d['distance'])
                decision_msg['action'] = 'EMERGENCY_STOP'
                decision_msg['speed_limit'] = 0.0
                decision_msg['target'] = closest['class']
                decision_msg['distance'] = closest['distance']
                decision_msg['reason'] = f"CRITICAL HAZARD: {closest['class']} at {closest['distance']}m"

                hud_color = (0, 0, 255)
                hud_text = f"AI DECISION: EMERGENCY BRAKE! [{closest['class'].upper()} @ {closest['distance']}m]"

                stop_twist = Twist()
                self.cmd_vel_pub.publish(stop_twist)
                self._dispatch_speed_limit(0.0)

            elif yield_threats:
                closest = min(yield_threats, key=lambda d: d['distance'])
                safe_speed = max(0.4, min(1.2, 0.25 * closest['distance']))
                decision_msg['action'] = 'YIELD_AND_SLOW'
                decision_msg['speed_limit'] = round(safe_speed, 2)
                decision_msg['target'] = closest['class']
                decision_msg['distance'] = closest['distance']
                decision_msg['reason'] = f"YIELD: {closest['class']} at {closest['distance']}m -> Throttling to {safe_speed:.2f} m/s"

                hud_color = (0, 215, 255)
                hud_text = f"AI DECISION: YIELDING [{closest['class'].upper()} @ {closest['distance']}m -> {safe_speed:.2f} m/s]"

                self._dispatch_speed_limit(safe_speed)

            else:
                if self.last_decision_state != 'CLEAR':
                    self._dispatch_speed_limit(2.5)

            self.last_decision_state = decision_msg['action']

            # Publish Decision Telemetry
            dec_str = String()
            dec_str.data = json.dumps(decision_msg)
            self.decision_pub.publish(dec_str)

            # Publish Detection List
            det_str = String()
            det_str.data = json.dumps(detections_list)
            self.det_pub.publish(det_str)

            # 4. Project Vision Obstacles into Nav2 Costmap
            if PC2_AVAILABLE and len(obstacle_points) > 0:
                header = Header()
                header.stamp = msg.header.stamp
                header.frame_id = 'base_link'
                cloud_msg = pc2.create_cloud_xyz32(header, obstacle_points)
                self.vision_obstacles_pub.publish(cloud_msg)

            # 5. Render Tactical HUD Video Overlay
            for det in detections_list:
                x1, y1, x2, y2 = det['bbox']
                d = det.get('distance', 0.0)
                cls_name = det.get('class', 'obstacle')
                box_color = (0, 242, 254)
                if abs(det.get('lateral_x', 99)) <= 1.25:
                    box_color = (0, 0, 255) if d < 2.0 else (0, 215, 255)

                cv2.rectangle(color_frame, (x1, y1), (x2, y2), box_color, 2)
                label = f"{cls_name.upper()} {d:.1f}m"
                cv2.putText(color_frame, label, (x1, max(18, y1 - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

            # Draw AI Decision Banner
            cv2.rectangle(color_frame, (0, 0), (w, 32), (15, 20, 25), -1)
            cv2.putText(color_frame, hud_text, (12, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52, hud_color, 2, cv2.LINE_AA)

            out_msg = self.bridge.cv2_to_imgmsg(color_frame, encoding='bgr8')
            out_msg.header = msg.header
            self.image_pub.publish(out_msg)

        except Exception as e:
            self.get_logger().error(f'[VISION-AI] Perception loop exception: {e}', throttle_duration_sec=2.0)

    def _dispatch_speed_limit(self, speed):
        """Dispatches dynamic speed limit to Nav2 controller."""
        now = time.time()
        if (now - self.last_speed_pub_time) > 0.4 or abs(speed - self.last_speed_limit_published) > 0.2:
            if NAV2_SPEED_LIMIT_AVAILABLE and hasattr(self, 'speed_limit_pub'):
                lim = SpeedLimit()
                lim.percentage = False
                lim.speed_limit = float(speed)
                self.speed_limit_pub.publish(lim)
            self.last_speed_limit_published = speed
            self.last_speed_pub_time = now

    def _tactical_cv_detect(self, frame):
        """Tactical Computer Vision Engine (Zero-Dependency High-Speed CV Engine)."""
        detections = []
        h, w = frame.shape[:2]

        if self.latest_depth_img is not None and (time.time() - self.latest_depth_time) < 1.0:
            depth = cv2.resize(self.latest_depth_img, (w, h))
            mask = cv2.inRange(depth, 0.4, 7.5)
            mask[int(h * 0.85):, :] = 0  # ignore ground

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
            mask_clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 1200:
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    aspect = bh / float(bw)
                    cls_name = 'pedestrian' if aspect > 1.4 else ('vehicle' if bw > 140 else 'obstacle')
                    detections.append({
                        'class': cls_name,
                        'confidence': 0.82,
                        'bbox': [x, y, x + bw, y + bh]
                    })
        else:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 60, 160)
            edges[int(h * 0.70):, :] = 0  # ignore ground and road curbs

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
            dilated = cv2.dilate(edges, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)
                if area > 4500 and (y + bh) < int(h * 0.85):  # avoid ground texture
                    x, y, bw, bh = cv2.boundingRect(cnt)
                    detections.append({
                        'class': 'hazard_object',
                        'confidence': 0.75,
                        'bbox': [x, y, x + bw, y + bh]
                    })

        return detections


def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
