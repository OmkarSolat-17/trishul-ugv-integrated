"""TRISHUL - SLAM Launch (Member 3).

360 LiDAR mode (default): ros2 launch trishul_localization slam_launch.py use_sim_time:=true
Depth-scan mode: ros2 launch trishul_localization slam_launch.py scan_from_depth:=true
"""
import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction, ExecuteProcess
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_dir = get_package_share_directory("trishul_localization")
    slam_config = os.path.join(pkg_dir, "config", "slam_toolbox_online.yaml")

    use_sim_time = LaunchConfiguration("use_sim_time")
    scan_from_depth = LaunchConfiguration("scan_from_depth")
    depth_topic = LaunchConfiguration("depth_topic")
    depth_info_topic = LaunchConfiguration("depth_info_topic")

    args = [
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("scan_from_depth", default_value="false"),
        DeclareLaunchArgument("depth_topic", default_value="/camera/image_raw"),
        DeclareLaunchArgument("depth_info_topic", default_value="/camera/camera_info"),
    ]

    depth_to_scan = Node(
        package="depthimage_to_laserscan",
        executable="depthimage_to_laserscan_node",
        name="depth_to_scan",
        condition=IfCondition(scan_from_depth),
        remappings=[
            ("depth", depth_topic),
            ("depth_camera_info", depth_info_topic),
            ("scan", "/scan"),
        ],
        parameters=[{
            "use_sim_time": use_sim_time,
            "output_frame": "camera_link",
            "range_min": 0.2,
            "range_max": 15.0,
            "scan_height": 10,
        }],
        output="screen",
    )

    slam_toolbox = Node(
        package="slam_toolbox",
        executable="async_slam_toolbox_node",
        name="slam_toolbox",
        parameters=[slam_config, {"use_sim_time": use_sim_time}],
        output="screen",
    )

    configure_cmd = TimerAction(period=4.0, actions=[ExecuteProcess(
        cmd=["ros2", "lifecycle", "set", "/slam_toolbox", "configure"],
        output="screen")])

    activate_cmd = TimerAction(period=7.0, actions=[ExecuteProcess(
        cmd=["ros2", "lifecycle", "set", "/slam_toolbox", "activate"],
        output="screen")])

    return LaunchDescription(args + [
        depth_to_scan, slam_toolbox, configure_cmd, activate_cmd,
    ])
