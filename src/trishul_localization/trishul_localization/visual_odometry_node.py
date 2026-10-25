#!/usr/bin/env python3
"""TRISHUL - Visual Odometry with IMU fusion"""
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, Imu
from nav_msgs.msg import Odometry
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import cv2
import numpy as np
import math

class VisualOdometryNode(Node):
    def __init__(self):
        super().__init__("visual_odometry")
        self.declare_parameter("orb_features", 1500)
        self.declare_parameter("min_matches", 20)
        self.declare_parameter("scale_factor", 0.005)
        self.declare_parameter("imu_weight", 0.3)
        self.declare_parameter("use_imu_fusion", True)
        self.declare_parameter("publish_tf", False)
        self.declare_parameter("color_topic", "/camera/color/image_raw")
        self.declare_parameter("imu_topic", "/imu")
        self.publish_tf_enabled = self.get_parameter("publish_tf").value
        self.orb_features = self.get_parameter("orb_features").value
        self.min_matches = self.get_parameter("min_matches").value
        self.scale = self.get_parameter("scale_factor").value
        self.imu_weight = self.get_parameter("imu_weight").value
        self.use_imu = self.get_parameter("use_imu_fusion").value
        color_topic = self.get_parameter("color_topic").value
        imu_topic = self.get_parameter("imu_topic").value
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.prev_gray = None
        self.prev_kp = None
        self.prev_desc = None
        self.orb = cv2.ORB_create(nfeatures=self.orb_features)
        self.bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        self.imu_yaw_rate = 0.0
        self.imu_valid = False
        self.bridge = CvBridge()
        self.tf_broadcaster = TransformBroadcaster(self)
        self.rgb_sub = self.create_subscription(
            Image, color_topic, self.image_callback, 10)
        self.imu_sub = self.create_subscription(
            Imu, imu_topic, self.imu_callback, 10)
        self.odom_pub = self.create_publisher(Odometry, "/vo/odom", 10)
        self.get_logger().info("Visual Odometry READY")

    def imu_callback(self, msg):
        self.imu_yaw_rate = msg.angular_velocity.z
        self.imu_valid = True

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        except Exception:
            return
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        curr_kp = self.orb.detect(gray, None)
        curr_kp, curr_desc = self.orb.compute(gray, curr_kp)
        if (self.prev_gray is not None and self.prev_desc is not None
                and curr_desc is not None
                and len(curr_desc) > self.min_matches
                and len(self.prev_desc) > self.min_matches):
            matches = self.bf.match(self.prev_desc, curr_desc)
            matches = sorted(matches, key=lambda m: m.distance)
            good = matches[:min(80, len(matches))]
            if len(good) >= self.min_matches:
                src = np.float32([self.prev_kp[m.queryIdx].pt for m in good]).reshape(-1,1,2)
                dst = np.float32([curr_kp[m.trainIdx].pt for m in good]).reshape(-1,1,2)
                M, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC)
                if M is not None:
                    dx = M[0, 2] * self.scale
                    dy = M[1, 2] * self.scale
                    dtheta_vo = math.atan2(M[1, 0], M[0, 0])
                    if self.use_imu and self.imu_valid:
                        dtheta = (1-self.imu_weight)*dtheta_vo + self.imu_weight*self.imu_yaw_rate*0.1
                    else:
                        dtheta = dtheta_vo
                    self.theta += dtheta
                    self.x += dx*math.cos(self.theta) - dy*math.sin(self.theta)
                    self.y += dx*math.sin(self.theta) + dy*math.cos(self.theta)
        self.prev_gray = gray
        self.prev_kp = curr_kp
        self.prev_desc = curr_desc
        self.publish_odom(msg.header.stamp)
        if self.publish_tf_enabled:
            self.publish_tf(msg.header.stamp)

    def publish_odom(self, stamp):
        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        q = [0.0, 0.0, math.sin(self.theta/2), math.cos(self.theta/2)]
        odom.pose.pose.orientation.x = q[0]
        odom.pose.pose.orientation.y = q[1]
        odom.pose.pose.orientation.z = q[2]
        odom.pose.pose.orientation.w = q[3]
        odom.twist.twist.angular.z = self.imu_yaw_rate
        self.odom_pub.publish(odom)

    def publish_tf(self, stamp):
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = "odom"
        t.child_frame_id = "base_link"
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        q = [0.0, 0.0, math.sin(self.theta/2), math.cos(self.theta/2)]
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]
        self.tf_broadcaster.sendTransform(t)

def main(args=None):
    rclpy.init(args=args)
    node = VisualOdometryNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
