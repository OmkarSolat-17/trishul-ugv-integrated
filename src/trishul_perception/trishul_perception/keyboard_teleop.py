import sys
import select
import termios
import tty
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

INSTRUCTIONS = """
---------------------------
TRISHUL UGV Keyboard Teleop
---------------------------
Moving around:
   w
a  s  d
   x

w/x : increase/decrease linear velocity (0.05 m/s)
a/d : increase/decrease angular velocity (0.1 rad/s)
space/s : force stop
Ctrl-C to quit
"""

class UGVKeyboardTeleop(Node):
    def __init__(self):
        super().__init__('ugv_keyboard_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.linear_step = 0.05
        self.angular_step = 0.1
        self.max_linear = 0.26
        self.max_angular = 1.0

    def publish_cmd(self, linear, angular):
        msg = Twist()
        msg.linear.x = float(max(-self.max_linear, min(self.max_linear, linear)))
        msg.angular.z = float(max(-self.max_angular, min(self.max_angular, angular)))
        self.pub.publish(msg)

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

def main(args=None):
    rclpy.init(args=args)
    node = UGVKeyboardTeleop()
    settings = termios.tcgetattr(sys.stdin)
    linear = 0.0
    angular = 0.0
    print(INSTRUCTIONS)

    try:
        while rclpy.ok():
            key = get_key(settings)
            if key == 'w':
                linear = min(node.max_linear, linear + node.linear_step)
            elif key == 'x':
                linear = max(-node.max_linear, linear - node.linear_step)
            elif key == 'a':
                angular = min(node.max_angular, angular + node.angular_step)
            elif key == 'd':
                angular = max(-node.max_angular, angular - node.angular_step)
            elif key in ('s', ' '):
                linear = 0.0
                angular = 0.0
            elif key == '\x03':
                break
            node.publish_cmd(linear, angular)
    except Exception as e:
        print(e)
    finally:
        node.publish_cmd(0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
