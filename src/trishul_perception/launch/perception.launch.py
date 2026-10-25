import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_perception = get_package_share_directory('trishul_perception')
    best_model = os.path.join(pkg_perception, 'models', 'best.pt')
    default_model = (
        best_model if os.path.exists(best_model)
        else os.path.join(pkg_perception, 'models', 'yolo26n.pt')
    )

    use_sim_time = LaunchConfiguration('use_sim_time')
    model_path = LaunchConfiguration('model_path')
    color_topic = LaunchConfiguration('color_topic')
    depth_topic = LaunchConfiguration('depth_topic')
    output_topic = LaunchConfiguration('output_topic')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('model_path', default_value=default_model),
        DeclareLaunchArgument('color_topic', default_value='/camera/color/image_raw'),
        DeclareLaunchArgument('depth_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('input_topic', default_value='/camera/image_raw'),
        DeclareLaunchArgument('output_topic', default_value='/ugv/combined/image'),

        Node(
            package='trishul_perception',
            executable='image_processor',
            name='image_processor',
            output='screen',
            parameters=[{
                'use_sim_time': use_sim_time,
                'model_path': model_path,
                'color_topic': color_topic,
                'depth_topic': depth_topic,
                'output_topic': output_topic,
            }],
        ),
    ])
