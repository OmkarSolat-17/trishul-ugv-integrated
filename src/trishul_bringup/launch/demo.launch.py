import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node


def _resolve_workspace_root(pkg_share: str) -> str:
    candidates = [
        os.environ.get('TRISHUL_WORKSPACE', ''),
        os.path.abspath(os.path.join(pkg_share, '..', '..', '..', '..')),
        os.getcwd(),
    ]
    for cand in candidates:
        if cand and os.path.isdir(os.path.join(cand, 'worlds')):
            return os.path.abspath(cand)
    return os.path.abspath(os.path.join(pkg_share, '..', '..', '..', '..'))


def generate_launch_description():
    pkg_bringup = get_package_share_directory('trishul_bringup')
    pkg_nav = get_package_share_directory('trishul_navigation')
    pkg_perception = get_package_share_directory('trishul_perception')

    ws_root = _resolve_workspace_root(pkg_bringup)
    city_world_path = os.path.join(ws_root, 'worlds', 'city_normal.sdf.xacro')
    tb3_world_path = '/opt/ros/jazzy/share/nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro'

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    use_custom_world = LaunchConfiguration('use_custom_world')
    launch_perception = LaunchConfiguration('launch_perception')
    launch_dashboard = LaunchConfiguration('launch_dashboard')
    dashboard_port = LaunchConfiguration('dashboard_port')
    slam = LaunchConfiguration('slam')

    in_xvfb = 'True' if os.environ.get('TRISHUL_XVFB_ACTIVE') == '1' else 'False'

    effective_rviz = PythonExpression([
        "'False' if ('", in_xvfb, "' == 'True' or '",
        headless, "'.lower() in ('true', '1', 'yes')) "
        "else ('True' if '", use_rviz, "'.lower() in ('true', '1', 'yes', 'auto') else 'False')"
    ])

    world_file = PythonExpression([
        f"'{city_world_path}' if '", use_custom_world,
        f"'.lower() == 'true' else '{tb3_world_path}'"
    ])

    slam_enabled = PythonExpression([
        "'True' if '", slam, "'.lower() == 'true' else "
        "('True' if '", use_custom_world, "'.lower() == 'true' else 'False')"
    ])

    use_fallback_map = PythonExpression([
        "'False' if (", slam_enabled, ") == 'True' else 'True'"
    ])

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation clock if true',
        ),
        DeclareLaunchArgument(
            'headless', default_value='False',
            description='Run Gazebo in headless mode',
        ),
        DeclareLaunchArgument(
            'use_rviz', default_value='auto',
            description='Launch RViz2 visualization',
        ),
        DeclareLaunchArgument(
            'use_custom_world', default_value='false',
            description='Set to true to use custom city world',
        ),
        DeclareLaunchArgument(
            'launch_perception', default_value='true',
            description='Whether to start the YOLO perception node',
        ),
        DeclareLaunchArgument(
            'launch_dashboard', default_value='true',
            description='Whether to start Trishul Mission Control Web Dashboard',
        ),
        DeclareLaunchArgument(
            'dashboard_port', default_value='8090',
            description='Port for Mission Control Web Dashboard',
        ),
        DeclareLaunchArgument(
            'slam', default_value='False',
            description='Whether to enable SLAM mapping',
        ),

        LogInfo(msg=['[TRISHUL BRINGUP] Initializing complete UGV platform...']),

        # 1. Navigation & Simulation Subsystem
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'headless': headless,
                'use_rviz': effective_rviz,
                'world': world_file,
                'slam': slam_enabled,
            }.items(),
        ),

        # 2. Self-Healing System Readiness & Lifecycle Coordinator
        Node(
            package='trishul_bringup',
            executable='system_coordinator',
            name='trishul_system_coordinator',
            parameters=[{
                'use_sim_time': use_sim_time,
                'slam_enabled': slam_enabled,
            }],
            output='screen',
        ),

        # 3. Perception Subsystem (YOLO & 3D Depth Decision Engine)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_perception, 'launch', 'perception.launch.py')
            ),
            condition=IfCondition(launch_perception),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'color_topic': '/camera/color/image_raw',
                'depth_topic': '/camera/image_raw',
                'output_topic': '/ugv/combined/image',
            }.items(),
        ),

        # 4. Extra Camera Bridge (color + rear streams for TB3 custom xacro)
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='trishul_camera_bridge',
            arguments=[
                '/camera/color/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/camera/color/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
                '/camera/rear/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/camera/rear/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        # 5. TRISHUL UGV Mission Control Web Dashboard Node
        Node(
            package='trishul_bringup',
            executable='dashboard_server',
            name='trishul_dashboard_server',
            condition=IfCondition(launch_dashboard),
            parameters=[{
                'use_sim_time': use_sim_time,
                'port': dashboard_port,
                'web_root': os.path.join(pkg_bringup, 'web'),
                'slam_mode': slam_enabled,
                'use_fallback_map': use_fallback_map,
            }],
            output='screen',
        ),
    ])
