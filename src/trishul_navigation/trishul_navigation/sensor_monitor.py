import math

from geometry_msgs.msg import Twist
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class SensorMonitor(Node):
    def __init__(self):
        super().__init__('trishul_sensor_monitor')

        # Parameters
        self.declare_parameter('enable_emergency_stop', True)
        self.declare_parameter('danger_distance', 0.25)
        self.declare_parameter('warning_distance', 0.50)

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.cmd_vel_pub = self.create_publisher(
            Twist,
            '/cmd_vel',
            10
        )

        self.in_danger_state = False
        self.get_logger().info('Trishul active sensor monitor & safety controller started')

    def scan_callback(self, msg):
        valid_readings = [
            (distance, index)
            for index, distance in enumerate(msg.ranges)
            if math.isfinite(distance)
            and msg.range_min <= distance <= msg.range_max
        ]

        if not valid_readings:
            self.get_logger().warning(
                'No valid laser readings available',
                throttle_duration_sec=2.0
            )
            return

        nearest, index = min(valid_readings, key=lambda item: item[0])

        angle = math.degrees(
            msg.angle_min + index * msg.angle_increment
        )

        angle = (angle + 180) % 360 - 180

        if -15 <= angle <= 15:
            direction = 'FRONT'
        elif 15 < angle <= 60:
            direction = 'FRONT-LEFT'
        elif 60 < angle <= 120:
            direction = 'LEFT'
        elif -60 <= angle < -15:
            direction = 'FRONT-RIGHT'
        elif -120 <= angle < -60:
            direction = 'RIGHT'
        else:
            direction = 'OTHER'

        danger_dist = self.get_parameter('danger_distance').value
        warning_dist = self.get_parameter('warning_distance').value
        enable_e_stop = self.get_parameter('enable_emergency_stop').value

        if nearest < danger_dist:
            status = 'DANGER'
        elif nearest < warning_dist:
            status = 'WARNING'
        else:
            status = 'CLEAR'

        # Active Safety Stop Logic
        if status == 'DANGER' and direction in ('FRONT', 'FRONT-LEFT', 'FRONT-RIGHT'):
            if enable_e_stop:
                stop_msg = Twist()
                stop_msg.linear.x = 0.0
                stop_msg.linear.y = 0.0
                stop_msg.linear.z = 0.0
                stop_msg.angular.x = 0.0
                stop_msg.angular.y = 0.0
                stop_msg.angular.z = 0.0
                self.cmd_vel_pub.publish(stop_msg)

            self.in_danger_state = True
            self.get_logger().error(
                f'EMERGENCY STOP! Obstacle in {direction} ({angle:.1f} deg) at {nearest:.2f} m!',
                throttle_duration_sec=1.0
            )
        else:
            if self.in_danger_state and status == 'CLEAR':
                self.in_danger_state = False
                self.get_logger().info('Obstacle cleared. Path is open.')

            self.get_logger().info(
                f'Status: {status} | '
                f'Direction: {direction} ({angle:.1f} deg) | '
                f'Distance: {nearest:.2f} m',
                throttle_duration_sec=1.0
            )


def main(args=None):
    rclpy.init(args=args)
    node = SensorMonitor()

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
