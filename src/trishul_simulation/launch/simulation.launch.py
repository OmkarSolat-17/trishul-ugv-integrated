import os
import re
import shutil
import subprocess

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    SetEnvironmentVariable,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _resolve_workspace_root(pkg_sim: str) -> str:
    """Resolve workspace root containing models/ and worlds/ across any user machine."""
    candidates = [
        os.environ.get('TRISHUL_WORKSPACE', ''),
        os.path.abspath(os.path.join(pkg_sim, '..', '..', '..', '..')),
        os.getcwd(),
    ]
    for cand in candidates:
        has_dirs = (
            cand
            and os.path.isdir(os.path.join(cand, 'models'))
            and os.path.isdir(os.path.join(cand, 'worlds'))
        )
        if has_dirs:
            return os.path.abspath(cand)
    return os.path.abspath(os.path.join(pkg_sim, '..', '..', '..', '..'))


def _probe_display_opengl_33() -> bool:
    """Return True if current DISPLAY supports OpenGL >= 3.3 without drisw/GLX failure."""
    if os.environ.get('TRISHUL_XVFB_ACTIVE') == '1':
        return True
    if not os.environ.get('DISPLAY'):
        return False
    glxinfo_bin = shutil.which('glxinfo')
    if not glxinfo_bin:
        # On WSL2 (/dev/dxg) without glxinfo we cannot trust hardware GLX; prefer safe Xvfb
        return not os.path.exists('/dev/dxg')
    try:
        res = subprocess.run(
            [glxinfo_bin, '-B'],
            capture_output=True,
            text=True,
            timeout=3.0,
            check=False,
        )
        out = (res.stdout or '') + '\n' + (res.stderr or '')
        if res.returncode != 0:
            return False
        if re.search(r'failed to create|unable to open display|error', out, re.IGNORECASE):
            return False
        m = re.search(r'OpenGL core profile version string:\s*(\d+)\.(\d+)', out)
        if not m:
            m = re.search(r'OpenGL version string:\s*(\d+)\.(\d+)', out)
        if not m:
            return False
        major, minor = int(m.group(1)), int(m.group(2))
        return (major > 3) or (major == 3 and minor >= 3)
    except Exception:
        return False


def _launch_gazebo_setup(context, pkg_ros_gz_sim: str, worlds_dir: str):
    world_val = LaunchConfiguration('world').perform(context).strip()
    headless_str = LaunchConfiguration('headless').perform(context).strip().lower()
    headless_render_str = (
        LaunchConfiguration('headless_rendering').perform(context).strip().lower()
    )

    headless = headless_str in ('true', '1', 'yes')
    headless_rendering = headless_render_str in ('true', '1', 'yes')

    if os.path.isabs(world_val) and os.path.exists(world_val):
        resolved_world = world_val
    else:
        resolved_world = os.path.join(worlds_dir, world_val)

    gl_ok = _probe_display_opengl_33()
    actions = []

    if not gl_ok:
        # Hardware/current GLX cannot provide OpenGL 3.3+ (common on WSL2).
        # Force server-only (-s) + Mesa llvmpipe under Xvfb so Ogre2 never segfaults.
        headless = True
        xvfb_bin = shutil.which('xvfb-run')
        gz_env = dict(os.environ)
        gz_env.pop('MESA_D3D12_DEFAULT_ADAPTER_NAME', None)
        gz_env['LIBGL_ALWAYS_SOFTWARE'] = '1'
        gz_env['GALLIUM_DRIVER'] = 'llvmpipe'
        gz_env.setdefault('LP_NUM_THREADS', '4')
        gz_env['QT_XCB_GL_INTEGRATION'] = 'none'

        gz_cmd = ['gz', 'sim', '-r', '-s', '-v', '3']
        if headless_rendering and not xvfb_bin:
            gz_cmd.append('--headless-rendering')
        gz_cmd.append(resolved_world)

        if xvfb_bin and os.environ.get('TRISHUL_XVFB_ACTIVE') != '1':
            actions.append(LogInfo(msg=[
                '[TRISHUL SIM] Launching Gazebo Harmonic server under xvfb-run + Mesa llvmpipe: ',
                resolved_world,
            ]))
            full_cmd = [
                xvfb_bin, '-a',
                '-s', '-screen 0 1280x1024x24 +extension GLX +render -noreset',
            ] + gz_cmd
            actions.append(ExecuteProcess(cmd=full_cmd, additional_env=gz_env, output='screen'))
            return actions
        else:
            actions.append(LogInfo(msg=[
                '[TRISHUL SIM] Launching Gazebo Harmonic server with Mesa llvmpipe fallback: ',
                resolved_world,
            ]))
            actions.append(ExecuteProcess(cmd=gz_cmd, additional_env=gz_env, output='screen'))
            return actions

    flags = ['-r', '-v', '3']
    if headless:
        flags.append('-s')
        if headless_rendering:
            flags.append('--headless-rendering')

    gz_args_str = ' '.join(flags) + f' {resolved_world}'
    mode_label = 'HEADLESS SERVER (-s)' if headless else 'GUI + SERVER'
    actions.append(LogInfo(msg=[
        f'[TRISHUL SIM] Launching Gazebo Harmonic ({mode_label}): {resolved_world}'
    ]))
    actions.append(
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={
                'gz_args': gz_args_str,
                'on_exit_shutdown': 'false',
            }.items(),
        )
    )
    return actions


def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_sim = get_package_share_directory('trishul_simulation')

    ws_root = _resolve_workspace_root(pkg_sim)
    models_dir = os.path.join(ws_root, 'models')
    worlds_dir = os.path.join(ws_root, 'worlds')
    config_path = os.path.join(pkg_sim, 'config', 'ros_gz_bridge.yaml')

    world_arg = DeclareLaunchArgument(
        'world',
        default_value='city_normal.sdf',
        description='World file name (city_normal.sdf or trishul_final.sdf) or full path',
    )

    headless_arg = DeclareLaunchArgument(
        'headless',
        default_value='false',
        description='Whether to run Gazebo in server-only headless mode (-s)',
    )

    headless_rendering_arg = DeclareLaunchArgument(
        'headless_rendering',
        default_value='false',
        description='Pass --headless-rendering (EGL) to Gazebo server when not using Xvfb/GLX',
    )

    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation clock if true',
    )

    existing_gz_res = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    gz_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=f'{models_dir}:{worlds_dir}:{existing_gz_res}',
    )

    existing_sdf_path = os.environ.get('SDF_PATH', '')
    sdf_resource_path = SetEnvironmentVariable(
        name='SDF_PATH',
        value=f'{models_dir}:{worlds_dir}:{existing_sdf_path}',
    )

    gz_sim_opaque = OpaqueFunction(
        function=_launch_gazebo_setup,
        kwargs={'pkg_ros_gz_sim': pkg_ros_gz_sim, 'worlds_dir': worlds_dir},
    )

    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='trishul_gz_bridge',
        parameters=[{
            'config_file': config_path,
            'use_sim_time': LaunchConfiguration('use_sim_time'),
        }],
        output='screen',
    )

    return LaunchDescription([
        world_arg,
        headless_arg,
        headless_rendering_arg,
        use_sim_time_arg,
        gz_resource_path,
        sdf_resource_path,
        gz_sim_opaque,
        bridge,
    ])
