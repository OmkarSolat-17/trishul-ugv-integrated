import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class SensorMonitor(Node):
    def __init__(self):
        super().__init__('trishul_sensor_monitor')

        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.get_logger().info('Trishul sensor monitor started')

    def scan_callback(self, msg):
        valid_readings = [
            (distance, index)
            for index, distance in enumerate(msg.ranges)
            if math.isfinite(distance)
            and msg.range_min <= distance <= msg.range_max
        ]

        if not valid_readings:
            self.get_logger().warning(
                'No valid laser readings available'
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

        if nearest < 0.25:
            status = 'DANGER'
        elif nearest < 0.50:
            status = 'WARNING'
        else:
            status = 'CLEAR'

        self.get_logger().info(
            f'Status: {status} | '
            f'Direction: {direction} ({angle:.1f} deg) | '
            f'Distance: {nearest:.2f} m'
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
