"""TRISHUL - Visual Odometry Launch"""
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package="trishul_localization",
            executable="visual_odometry",
            parameters=[{"orb_features": 1500, "min_matches": 20,
                         "scale_factor": 0.005, "imu_weight": 0.3,
                         "use_imu_fusion": True}],
            output="screen"),
    ])
