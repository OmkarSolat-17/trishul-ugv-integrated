import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist

class UGVSafetyController(Node):
    def __init__(self):
        super().__init__('ugv_safety_controller')
        self.declare_parameter('stop_distance', 0.30)
        self.stop_dist = self.get_parameter('stop_distance').value

        self.front_clearance = None
        self.requested_twist = Twist()

        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.cmd_sub = self.create_subscription(Twist, '/ugv/cmd_vel_request', self.cmd_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(0.05, self.control_loop)
        self.get_logger().info('UGV Safety Controller initialized (using geometry_msgs/Twist).')

    def scan_callback(self, msg):
        front = []
        for i, dist in enumerate(msg.ranges):
            angle = msg.angle_min + i * msg.angle_increment
            if abs(math.atan2(math.sin(angle), math.cos(angle))) <= math.radians(25):
                if math.isfinite(dist) and msg.range_min <= dist <= msg.range_max:
                    front.append(dist)
        self.front_clearance = min(front) if front else None

    def cmd_callback(self, msg):
        self.requested_twist = msg

    def control_loop(self):
        cmd = Twist()
        if self.front_clearance is not None and self.front_clearance < self.stop_dist:
            if self.requested_twist.linear.x > 0:
                self.get_logger().warning(
                    f'Safety intervention: obstacle at {self.front_clearance:.2f}m. Halting forward motion!',
                    throttle_duration_sec=1.0
                )
                cmd.linear.x = 0.0
                cmd.angular.z = self.requested_twist.angular.z
                self.cmd_pub.publish(cmd)
                return
        self.cmd_pub.publish(self.requested_twist)

def main(args=None):
    rclpy.init(args=args)
    node = UGVSafetyController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
