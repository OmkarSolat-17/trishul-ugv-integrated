import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _maybe_launch_rviz(context, pkg_nav2_bringup: str, rviz_config_file: str):
    use_rviz_str = LaunchConfiguration('use_rviz').perform(context).strip().lower()
    headless_str = LaunchConfiguration('headless').perform(context).strip().lower()
    use_sim_time_val = LaunchConfiguration('use_sim_time')

    is_headless = headless_str in ('true', '1', 'yes')
    in_xvfb = os.environ.get('TRISHUL_XVFB_ACTIVE') == '1'
    has_display = bool(os.environ.get('DISPLAY')) and not in_xvfb

    if use_rviz_str == 'auto':
        should_rviz = (not is_headless) and has_display
    else:
        should_rviz = (use_rviz_str in ('true', '1', 'yes')) and has_display

    if not should_rviz:
        return []

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav2_bringup, 'launch', 'rviz_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time_val,
                'rviz_config': rviz_config_file,
            }.items(),
        )
    ]


def generate_launch_description():
    pkg_bringup = get_package_share_directory('trishul_bringup')
    pkg_sim = get_package_share_directory('trishul_simulation')
    pkg_nav = get_package_share_directory('trishul_navigation')
    pkg_localization = get_package_share_directory('trishul_localization')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')
    pkg_slam_toolbox = get_package_share_directory('slam_toolbox')

    # Config paths
    slam_params_file = os.path.join(pkg_localization, 'config', 'slam_toolbox_online.yaml')
    nav2_params_file = os.path.join(pkg_nav, 'config', 'nav2_params_4wd.yaml')
    rviz_config_file = os.path.join(pkg_nav, 'rviz', 'trishul_nav.rviz')

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    world = LaunchConfiguration('world')
    launch_perception = LaunchConfiguration('launch_perception')
    launch_dashboard = LaunchConfiguration('launch_dashboard')
    dashboard_port = LaunchConfiguration('dashboard_port')

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation clock if true',
        ),
        DeclareLaunchArgument(
            'headless', default_value='False',
            description='Run Gazebo in server-only headless mode (-s)',
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='auto',
            description='Launch RViz2 visualization (auto disables RViz in headless/Xvfb mode)',
        ),
        DeclareLaunchArgument(
            'world', default_value='city_normal.sdf',
            description='City world SDF file (city_normal.sdf or trishul_final.sdf)',
        ),
        DeclareLaunchArgument(
            'launch_perception', default_value='true',
            description='Whether to start the Vision-AI / YOLO perception node',
        ),
        DeclareLaunchArgument(
            'launch_dashboard', default_value='true',
            description='Whether to start Trishul Mission Control Web Dashboard',
        ),
        DeclareLaunchArgument(
            'dashboard_port', default_value='8090',
            description='Port for Mission Control Web Dashboard',
        ),

        LogInfo(msg=['[TRISHUL BRINGUP] Initializing 4WD City Simulation Profile...']),

        # 1. Gazebo Harmonic City Simulation with 4WD Model and ROS-GZ Bridge (t = 0.0s)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_sim, 'launch', 'simulation.launch.py')
            ),
            launch_arguments={
                'world': world,
                'headless': headless,
                'use_sim_time': use_sim_time,
            }.items(),
        ),

        # 2. Static Transform Publishers for 4WD UGV Kinematic Links (t = 0.0s)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_base_footprint_to_base_link',
            arguments=[
                '--frame-id', 'base_footprint',
                '--child-frame-id', 'base_link',
                '--x', '0', '--y', '0', '--z', '0',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_base_link_to_base_scan',
            arguments=[
                '--frame-id', 'base_link',
                '--child-frame-id', 'base_scan',
                '--x', '0.18', '--y', '0', '--z', '0.20',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_base_link_to_camera_link',
            arguments=[
                '--frame-id', 'base_link',
                '--child-frame-id', 'camera_link',
                '--x', '0.32', '--y', '0', '--z', '0.12',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_camera_link_to_depth',
            arguments=[
                '--frame-id', 'camera_link',
                '--child-frame-id', 'camera_depth_frame',
                '--x', '0', '--y', '0', '--z', '0',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_camera_link_to_rgb',
            arguments=[
                '--frame-id', 'camera_link',
                '--child-frame-id', 'camera_rgb_frame',
                '--x', '0', '--y', '0', '--z', '0',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf_base_link_to_imu',
            arguments=[
                '--frame-id', 'base_link',
                '--child-frame-id', 'imu_link',
                '--x', '0', '--y', '0', '--z', '0',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        # 3. SLAM Toolbox Online Mapping (staggered so /clock & odom->base_link are live)
        TimerAction(
            period=2.5,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(pkg_slam_toolbox, 'launch', 'online_async_launch.py')
                    ),
                    launch_arguments={
                        'use_sim_time': use_sim_time,
                        'slam_params_file': slam_params_file,
                        'autostart': 'true',
                    }.items(),
                ),
            ],
        ),

        # 4. Nav2 Navigation Stack (staggered so map->odom->base_link & /map are ready)
        TimerAction(
            period=5.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        os.path.join(pkg_nav2_bringup, 'launch', 'navigation_launch.py')
                    ),
                    launch_arguments={
                        'use_sim_time': use_sim_time,
                        'params_file': nav2_params_file,
                        'autostart': 'true',
                    }.items(),
                ),
            ],
        ),

        # 5. Self-Healing System Readiness & Lifecycle Coordinator
        Node(
            package='trishul_bringup',
            executable='system_coordinator',
            name='trishul_system_coordinator',
            parameters=[{
                'use_sim_time': use_sim_time,
                'slam_enabled': True,
            }],
            output='screen',
        ),

        # 6. RViz2 Visualization (only when GUI display is active)
        OpaqueFunction(
            function=_maybe_launch_rviz,
            kwargs={
                'pkg_nav2_bringup': pkg_nav2_bringup,
                'rviz_config_file': rviz_config_file,
            },
        ),

        # 7. Perception Subsystem (Vision-AI & YOLO Tactical Decision Engine)
        Node(
            package='trishul_perception',
            executable='image_processor',
            name='image_processor',
            condition=IfCondition(launch_perception),
            parameters=[{
                'use_sim_time': use_sim_time,
                'color_topic': '/camera/color/image_raw',
                'depth_topic': '/camera/image_raw',
                'output_topic': '/ugv/combined/image',
                'detections_topic': '/ugv/detections',
                'decision_topic': '/ugv/yolo_decision',
                'vision_obstacles_topic': '/ugv/vision_obstacles',
                'target_cruise_speed': 2.5,
            }],
            output='screen',
        ),

        # 8. Active Safety Proximity Monitor
        Node(
            package='trishul_navigation',
            executable='sensor_monitor',
            name='trishul_sensor_monitor',
            parameters=[{
                'use_sim_time': use_sim_time,
                'danger_distance': 0.35,
                'warning_distance': 0.60,
            }],
            output='screen',
        ),

        # 9. TRISHUL UGV Mission Control Web Dashboard Server
        Node(
            package='trishul_bringup',
            executable='dashboard_server',
            name='trishul_dashboard_server',
            condition=IfCondition(launch_dashboard),
            parameters=[{
                'use_sim_time': use_sim_time,
                'port': dashboard_port,
                'web_root': os.path.join(pkg_bringup, 'web'),
                'slam_mode': True,
                'use_fallback_map': False,
            }],
            output='screen',
        ),
    ])
