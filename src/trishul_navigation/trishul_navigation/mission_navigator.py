import math
import sys
import time

from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
import rclpy


def create_pose(navigator, x, y, yaw_deg=0.0):
    """Create a PoseStamped message synchronized with simulation clock."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = navigator.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.position.z = 0.01

    yaw_rad = math.radians(yaw_deg)
    pose.pose.orientation.z = math.sin(yaw_rad / 2.0)
    pose.pose.orientation.w = math.cos(yaw_rad / 2.0)
    return pose


def main(args=None):
    # Ensure simulation clock is enabled when communicating with Gazebo
    if args is None:
        args = sys.argv[1:]
    if not any('use_sim_time' in arg for arg in args):
        args = ['--ros-args', '-p', 'use_sim_time:=true'] + args

    rclpy.init(args=args)

    navigator = BasicNavigator()

    navigator.get_logger().info('Trishul Mission Navigator initialized.')

    # 1. Automatically set initial pose to match Gazebo spawn (-2.0, -0.5, yaw=0.0)
    init_pose = create_pose(navigator, -2.00, -0.50, yaw_deg=0.0)
    navigator.get_logger().info('Setting initial pose to match Gazebo: (-2.00, -0.50)...')
    navigator.setInitialPose(init_pose)

    navigator.get_logger().info('Waiting for Nav2 stack to become active...')
    navigator.waitUntilNav2Active()
    navigator.get_logger().info('Nav2 is fully active! Starting mission.')

    # 2. Define waypoints along open perimeter corridors (away from pillars)
    waypoints = [
        ('Corridor Alpha (North)', -2.0, 0.8, 90.0),
        ('Corridor Bravo (East)', -0.5, 1.8, 0.0),
        ('Base Return (Spawn)', -2.0, -0.5, 180.0),
    ]

    for name, x, y, yaw in waypoints:
        goal_pose = create_pose(navigator, x, y, yaw)
        navigator.get_logger().info(f'Navigating to {name}: ({x:.2f}, {y:.2f})')

        navigator.goToPose(goal_pose)

        last_feedback_time = time.time()
        while not navigator.isTaskComplete():
            feedback = navigator.getFeedback()
            current_time = time.time()

            if feedback and (current_time - last_feedback_time >= 2.0):
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
            navigator.get_logger().error(f'Navigation to {name} failed or timed out.')
            break

    navigator.get_logger().info('Trishul mission finished.')
    navigator.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
