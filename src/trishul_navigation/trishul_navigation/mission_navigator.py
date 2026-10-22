import math
import time

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy


def create_pose(navigator, x, y, yaw_deg=0.0):
    """Create a PoseStamped message on the 'map' frame."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.0

    yaw_rad = math.radians(yaw_deg)
    pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
    pose.pose.orientation.w = math.cos(yaw_rad / 2.0)
    return pose


def main(args=None):
    rclpy.init(args=args)

    navigator = BasicNavigator()

    navigator.get_logger().info('Trishul Mission Navigator initialized.')
    navigator.get_logger().info('Waiting for Nav2 stack to become active...')

    navigator.waitUntilNav2Active()
    navigator.get_logger().info('Nav2 is active. Starting mission.')

    # Define standard reconnaissance waypoints
    waypoints = [
        ('Checkpoint Alpha', 0.5, -0.5, 0.0),
        ('Checkpoint Bravo', 1.5, 0.5, 90.0),
        ('Base Return', -2.0, -0.5, 180.0),
    ]

    for name, x, y, yaw in waypoints:
        goal_pose = create_pose(navigator, x, y, yaw)
        navigator.get_logger().info(f'Navigating to {name}: ({x:.2f}, {y:.2f})')

        navigator.goToPose(goal_pose)

        last_feedback_time = time.time()
        while not navigator.isTaskComplete():
            feedback = navigator.getFeedback()
            current_time = time.time()

            if feedback and (current_time - last_feedback_time >= 3.0):
                last_feedback_time = current_time
                dist = feedback.distance_remaining
                navigator.get_logger().info(
                    f'En route to {name} | Distance remaining: {dist:.2f} m'
                )

            time.sleep(0.1)

        result = navigator.getResult()
        if result == TaskResult.SUCCEEDED:
            navigator.get_logger().info(f'Reached {name} successfully!')
        elif result == TaskResult.CANCELED:
            navigator.get_logger().warning(f'Mission to {name} was canceled.')
            break
        elif result == TaskResult.FAILED:
            navigator.get_logger().error(f'Navigation to {name} failed!')
            break

    navigator.get_logger().info('Trishul mission finished.')
    navigator.lifecycleShutdown()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
