import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_sim = get_package_share_directory('trishul_simulation')

    ws_root = os.path.abspath(os.path.join(pkg_sim, '..', '..', '..', '..'))
    if not os.path.isdir(os.path.join(ws_root, 'models')):
        ws_root = os.environ.get('TRISHUL_WORKSPACE', '/home/papa_ji/project/Trishul/merg-trishul')

    models_dir = os.path.join(ws_root, 'models')
    worlds_dir = os.path.join(ws_root, 'worlds')
    config_path = os.path.join(pkg_sim, 'config', 'ros_gz_bridge.yaml')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='city_normal.sdf',
        description='World file name (city_normal.sdf or trishul_final.sdf)'
    )

    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Whether to run Gazebo in headless mode'
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true'
    )

    world_name = LaunchConfiguration('world')
    world_file = PathJoinSubstitution([worlds_dir, world_name])

    existing_gz_res = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f"{models_dir}:{worlds_dir}:{existing_gz_res}"
    )

    existing_sdf_path = os.environ.get('SDF_PATH', '')
    sdf_resource_path = SetEnvironmentVariable(
        name='SDF_PATH',
        value=f"{models_dir}:{worlds_dir}:{existing_sdf_path}"
    )

    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={
            'gz_args': ['-r ', world_file],
            'on_exit_shutdown': 'false'
        }.items()
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{
            'config_file': config_path,
            'use_sim_time': LaunchConfiguration('use_sim_time')
        }],
        output='screen'
    )

    return LaunchDescription([
        world_arg,
        headless_arg,
        use_sim_time_arg,
        gz_resource_path,
        sdf_resource_path,
        gz_sim,
        bridge
    ])
