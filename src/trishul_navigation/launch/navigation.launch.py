import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_trishul_nav = get_package_share_directory('trishul_navigation')
    pkg_nav2_bringup = get_package_share_directory('nav2_bringup')

    # Default file paths
    default_params_file = os.path.join(
        pkg_trishul_nav, 'config', 'nav2_params.yaml'
    )
    default_rviz_config = os.path.join(
        pkg_trishul_nav, 'rviz', 'trishul_nav.rviz'
    )

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    rviz_config = LaunchConfiguration('rviz_config')
    headless = LaunchConfiguration('headless')
    use_rviz = LaunchConfiguration('use_rviz')

    # Declare launch arguments
    declare_use_sim_time_cmd = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation (Gazebo) clock if true',
    )

    declare_params_file_cmd = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the ROS 2 parameters file to use',
    )

    declare_rviz_config_cmd = DeclareLaunchArgument(
        'rviz_config',
        default_value=default_rviz_config,
        description='Full path to the RViz configuration file',
    )

    declare_headless_cmd = DeclareLaunchArgument(
        'headless',
        default_value='False',
        description='Whether to execute Gazebo in headless mode (False opens GUI)',
    )

    declare_use_rviz_cmd = DeclareLaunchArgument(
        'use_rviz',
        default_value='True',
        description='Whether to start RViz',
    )

    # Include Nav2 simulation bringup with Trishul parameters
    nav2_sim_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_nav2_bringup, 'launch', 'tb3_simulation_launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'rviz_config_file': rviz_config,
            'headless': headless,
            'use_rviz': use_rviz,
        }.items(),
    )

    # Trishul custom navigation nodes
    sensor_monitor_node = Node(
        package='trishul_navigation',
        executable='sensor_monitor',
        name='trishul_sensor_monitor',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    status_node = Node(
        package='trishul_navigation',
        executable='status_node',
        name='trishul_status_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    ld = LaunchDescription()

    # Add declarations
    ld.add_action(declare_use_sim_time_cmd)
    ld.add_action(declare_params_file_cmd)
    ld.add_action(declare_rviz_config_cmd)
    ld.add_action(declare_headless_cmd)
    ld.add_action(declare_use_rviz_cmd)

    # Add execution actions
    ld.add_action(nav2_sim_cmd)
    ld.add_action(sensor_monitor_node)
    ld.add_action(status_node)

    return ld
