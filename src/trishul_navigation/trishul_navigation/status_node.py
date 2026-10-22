import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TrishulStatusNode(Node):
    def __init__(self):
        super().__init__('trishul_status_node')

        self.publisher = self.create_publisher(
            String,
            'trishul/status',
            10
        )

        self.timer = self.create_timer(1.0, self.publish_status)

    def publish_status(self):
        msg = String()
        msg.data = 'Trishul navigation system is running'
        self.publisher.publish(msg)
        self.get_logger().info(msg.data)


def main(args=None):
    rclpy.init(args=args)
    node = TrishulStatusNode()

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
