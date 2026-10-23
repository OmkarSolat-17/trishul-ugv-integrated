import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node

def generate_launch_description():
    pkg_bringup = get_package_share_directory('trishul_bringup')
    pkg_nav = get_package_share_directory('trishul_navigation')
    pkg_perception = get_package_share_directory('trishul_perception')

    # Default paths
    city_world_path = '/home/papa_ji/project/Trishul/merg-trishul/worlds/city_normal.sdf.xacro'

    # Launch configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')
    use_custom_world = LaunchConfiguration('use_custom_world')
    launch_perception = LaunchConfiguration('launch_perception')
    launch_dashboard = LaunchConfiguration('launch_dashboard')
    dashboard_port = LaunchConfiguration('dashboard_port')
    slam = LaunchConfiguration('slam')

    # World selection
    world_file = PythonExpression([
        f"'{city_world_path}' if '", use_custom_world, "' == 'true' else '/opt/ros/jazzy/share/nav2_minimal_tb3_sim/worlds/tb3_sandbox.sdf.xacro'"
    ])

    slam_enabled = PythonExpression([
        "'True' if '", slam, "' == 'true' or '", slam, "' == 'True' else ('True' if '", use_custom_world, "' == 'true' else 'False')"
    ])

    return LaunchDescription([
        # Arguments
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use simulation clock if true'),
        DeclareLaunchArgument('headless', default_value='False',
                              description='Run Gazebo in headless mode'),
        DeclareLaunchArgument('use_rviz', default_value='True',
                              description='Launch RViz2 visualization'),
        DeclareLaunchArgument('use_custom_world', default_value='false',
                              description='Set to true to use custom city world'),
        DeclareLaunchArgument('launch_perception', default_value='true',
                              description='Whether to start the YOLO perception node'),
        DeclareLaunchArgument('launch_dashboard', default_value='true',
                              description='Whether to start Trishul Mission Control Web Dashboard'),
        DeclareLaunchArgument('dashboard_port', default_value='8090',
                              description='Port for Mission Control Web Dashboard'),
        DeclareLaunchArgument('slam', default_value='False',
                              description='Whether to enable SLAM mapping'),

        LogInfo(msg=['[TRISHUL BRINGUP] Initializing complete UGV platform...']),

        # 1. Navigation & Simulation Subsystem
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav, 'launch', 'navigation.launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'headless': headless,
                'use_rviz': use_rviz,
                'world': world_file,
                'slam': slam_enabled,
            }.items(),
        ),

        # 2. Perception Subsystem (YOLO detector)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_perception, 'launch', 'perception.launch.py')
            ),
            condition=IfCondition(launch_perception),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'input_topic': '/camera/image_raw',
                'output_topic': '/ugv/combined/image',
            }.items(),
        ),

        # 3. Camera Bridge: Gazebo -> ROS 2
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            name='trishul_camera_bridge',
            arguments=[
                '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
                '/camera/color/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/camera/color/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
                '/camera/rear/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
                '/camera/rear/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo',
            ],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ),

        # 4. TRISHUL UGV Mission Control Web Dashboard Node
        Node(
            package='trishul_bringup',
            executable='dashboard_server',
            name='trishul_dashboard_server',
            condition=IfCondition(launch_dashboard),
            parameters=[{
                'use_sim_time': use_sim_time,
                'port': dashboard_port,
                'web_root': os.path.join(pkg_bringup, 'web'),
            }],
            output='screen',
        ),
    ])
