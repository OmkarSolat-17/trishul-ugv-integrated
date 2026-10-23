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

    # Declare command parameters (default: cross-arena destination x=1.80, y=-0.50)
    navigator.declare_parameter('target_x', 1.80)
    navigator.declare_parameter('target_y', -0.50)
    navigator.declare_parameter('target_yaw', 0.0)

    target_x = float(navigator.get_parameter('target_x').value)
    target_y = float(navigator.get_parameter('target_y').value)
    target_yaw = float(navigator.get_parameter('target_yaw').value)

    # 1. Align initial position with Gazebo spawn point (-2.00, -0.50, yaw=0.0)
    init_pose = create_pose(navigator, -2.00, -0.50, yaw_deg=0.0)
    navigator.get_logger().info('Setting initial pose to match Gazebo: (-2.00, -0.50)...')
    navigator.setInitialPose(init_pose)

    # Allow AMCL and costmaps to settle
    time.sleep(1.0)

    navigator.get_logger().info('Waiting for Nav2 stack to become active...')
    navigator.waitUntilNav2Active()
    navigator.get_logger().info('Nav2 is active! Beginning navigation.')

    goal_pose = create_pose(navigator, target_x, target_y, target_yaw)
    navigator.get_logger().info(
        f'Target destination: ({target_x:.2f}, {target_y:.2f}) [yaw: {target_yaw:.1f} deg]'
    )

    navigator.goToPose(goal_pose)

    last_feedback_time = time.time()
    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        current_time = time.time()

        if feedback and (current_time - last_feedback_time >= 2.0):
            last_feedback_time = current_time
            dist = feedback.distance_remaining
            eta = feedback.estimated_time_remaining
            eta_sec = eta.sec + eta.nanosec * 1e-9 if hasattr(eta, 'sec') else float(eta)
            navigator.get_logger().info(
                f'Traversing to target | Distance remaining: {dist:.2f} m | ETA: {eta_sec:.1f} s'
            )

        time.sleep(0.1)

    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        navigator.get_logger().info(
            f'SUCCESS! Robot successfully reached target: ({target_x:.2f}, {target_y:.2f})!'
        )
    elif result == TaskResult.CANCELED:
        navigator.get_logger().warning('Mission was canceled.')
    elif result == TaskResult.FAILED:
        navigator.get_logger().error('Navigation task failed or timed out.')

    navigator.get_logger().info('Trishul mission finished.')
    navigator.destroy_node()
    if rclpy.ok():
        rclpy.shutdown()


if __name__ == '__main__':
    main()
