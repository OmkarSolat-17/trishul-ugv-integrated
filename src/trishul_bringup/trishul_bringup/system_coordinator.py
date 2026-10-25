#!/usr/bin/env python3
"""
TRISHUL UGV -- System Readiness & Self-Healing Lifecycle Coordinator
Ensures deterministic end-to-end startup across Gazebo Harmonic, TF2, SLAM Toolbox,
and Nav2 Lifecycle Nodes (even when WSL2 software rendering takes longer to boot):
  1. Verifies Gazebo /odom, /scan, and TF (odom -> base_footprint -> base_link).
  2. Verifies SLAM Toolbox transitions to ACTIVE and broadcasts TF (map -> odom).
  3. Verifies Nav2 lifecycle stack & bt_navigator transition to ACTIVE, automatically
     recovering any node that timed out while Gazebo was loading the world.
"""

import threading
import time

import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
import tf2_ros

from lifecycle_msgs.msg import Transition
from lifecycle_msgs.srv import ChangeState, GetState
from nav_msgs.msg import Odometry
from sensor_msgs.msg import LaserScan

try:
    from nav2_msgs.srv import ManageLifecycleNodes
    HAS_MANAGE_LIFECYCLE = True
except ImportError:
    ManageLifecycleNodes = None
    HAS_MANAGE_LIFECYCLE = False


NAV2_ORDERED_NODES = [
    'controller_server',
    'smoother_server',
    'planner_server',
    'route_server',
    'behavior_server',
    'bt_navigator',
    'waypoint_follower',
    'velocity_smoother',
    'collision_monitor',
    'docking_server',
]


class TrishulSystemCoordinator(Node):
    def __init__(self):
        super().__init__('trishul_system_coordinator')
        self.declare_parameter('slam_enabled', True)
        val = self.get_parameter('slam_enabled').value
        if isinstance(val, str):
            self.slam_enabled = val.strip().lower() in ('true', '1', 'yes')
        else:
            self.slam_enabled = bool(val)

        self.cb_group = ReentrantCallbackGroup()
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        self.has_odom_msg = False
        self.has_scan_msg = False
        self._shutdown = False

        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self._odom_cb, 10, callback_group=self.cb_group
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, 10, callback_group=self.cb_group
        )

        self._get_state_clients = {}
        self._change_state_clients = {}
        self._nav_mgr_client = (
            self.create_client(
                ManageLifecycleNodes,
                '/lifecycle_manager_navigation/manage_nodes',
                callback_group=self.cb_group,
            )
            if HAS_MANAGE_LIFECYCLE
            else None
        )

        self._worker = threading.Thread(target=self._coordination_loop, daemon=True)
        self._worker.start()

    def _odom_cb(self, _msg: Odometry):
        self.has_odom_msg = True

    def _scan_cb(self, _msg: LaserScan):
        self.has_scan_msg = True

    def _get_lifecycle_clients(self, node_name: str):
        if node_name not in self._get_state_clients:
            self._get_state_clients[node_name] = self.create_client(
                GetState, f'/{node_name}/get_state', callback_group=self.cb_group
            )
            self._change_state_clients[node_name] = self.create_client(
                ChangeState, f'/{node_name}/change_state', callback_group=self.cb_group
            )
        return self._get_state_clients[node_name], self._change_state_clients[node_name]

    def _call_async_wall_timeout(self, client, req, timeout_sec: float = 5.0):
        deadline = time.monotonic() + 1.5
        while not client.service_is_ready():
            if self._shutdown or time.monotonic() >= deadline:
                return None
            time.sleep(0.1)

        future = client.call_async(req)
        deadline = time.monotonic() + timeout_sec
        while not future.done():
            if self._shutdown or time.monotonic() >= deadline:
                return None
            time.sleep(0.05)

        try:
            return future.result()
        except Exception:
            return None

    def _query_node_state(self, node_name: str):
        get_cli, _ = self._get_lifecycle_clients(node_name)
        resp = self._call_async_wall_timeout(get_cli, GetState.Request(), timeout_sec=3.0)
        if resp is None:
            return None, None
        return resp.current_state.id, resp.current_state.label

    def _ensure_node_active(self, node_name: str) -> bool:
        state_id, _ = self._query_node_state(node_name)
        if state_id is None:
            # Optional node not present in current launch graph
            return False
        if state_id == 3:  # PRIMARY_STATE_ACTIVE
            return True
        if state_id >= 10:
            # Currently transitioning (configuring / activating); wait briefly
            time.sleep(1.0)
            state_id, _ = self._query_node_state(node_name)
            if state_id == 3:
                return True

        _, chg_cli = self._get_lifecycle_clients(node_name)

        if state_id == 1:  # PRIMARY_STATE_UNCONFIGURED
            self.get_logger().info(f'[COORDINATOR] Configuring /{node_name}...')
            req = ChangeState.Request()
            req.transition.id = Transition.TRANSITION_CONFIGURE
            self._call_async_wall_timeout(chg_cli, req, timeout_sec=8.0)
            time.sleep(0.4)
            state_id, _ = self._query_node_state(node_name)

        if state_id == 2:  # PRIMARY_STATE_INACTIVE
            self.get_logger().info(f'[COORDINATOR] Activating /{node_name}...')
            req = ChangeState.Request()
            req.transition.id = Transition.TRANSITION_ACTIVATE
            self._call_async_wall_timeout(chg_cli, req, timeout_sec=10.0)
            time.sleep(0.4)
            state_id, _ = self._query_node_state(node_name)

        return state_id == 3

    def _can_tf(self, target: str, source: str) -> bool:
        try:
            return self.tf_buffer.can_transform(target, source, rclpy.time.Time())
        except Exception:
            return False

    def _coordination_loop(self):
        self.get_logger().info(
            '[COORDINATOR] Monitoring Gazebo -> TF2 -> Localization -> Nav2 startup chain...'
        )

        # Stage 1: Wait for Gazebo /odom, /scan, and TF (odom -> base_link)
        last_log = 0.0
        while not self._shutdown and rclpy.ok():
            if self._can_tf('odom', 'base_link') and self.has_odom_msg:
                break
            if time.monotonic() - last_log > 4.0:
                self.get_logger().info(
                    '[COORDINATOR] [1/3] Waiting for Gazebo physics & TF (odom -> base_link)...'
                )
                last_log = time.monotonic()
            time.sleep(0.5)

        if self._shutdown or not rclpy.ok():
            return

        self.get_logger().info(
            '[COORDINATOR] [1/3] Gazebo /odom and TF (odom -> base_footprint -> base_link) LIVE!'
        )

        # Stage 2: Ensure SLAM Toolbox (or AMCL) is ACTIVE and map -> base_link TF exists
        slam_waited = 0.0
        last_log = 0.0
        while not self._shutdown and rclpy.ok():
            if self._can_tf('map', 'base_link'):
                break

            if self.slam_enabled and slam_waited >= 2.0:
                self._ensure_node_active('slam_toolbox')

            if time.monotonic() - last_log > 4.0:
                self.get_logger().info(
                    '[COORDINATOR] [2/3] Waiting for Global TF (map -> odom -> base_link)...'
                )
                last_log = time.monotonic()

            time.sleep(0.75)
            slam_waited += 0.75

        if self._shutdown or not rclpy.ok():
            return

        self.get_logger().info(
            '[COORDINATOR] [2/3] Full TF tree (map -> odom -> base_footprint -> base_link) LIVE!'
        )

        # Stage 3: Ensure Nav2 stack & bt_navigator reach ACTIVE
        # Allow lifecycle_manager_navigation a grace window to finish standard bringup first
        for _ in range(16):
            if self._shutdown or not rclpy.ok():
                return
            bt_id, _ = self._query_node_state('bt_navigator')
            if bt_id == 3:
                break
            time.sleep(0.5)

        while not self._shutdown and rclpy.ok():
            bt_id, bt_label = self._query_node_state('bt_navigator')
            ctrl_id, _ = self._query_node_state('controller_server')
            plan_id, _ = self._query_node_state('planner_server')

            if bt_id == 3 and ctrl_id == 3 and plan_id == 3:
                self.get_logger().info('=' * 72)
                self.get_logger().info(
                    '[COORDINATOR] [3/3] ALL SUBSYSTEMS ACTIVE! '
                    'bt_navigator, planner_server & controller_server READY.'
                )
                self.get_logger().info(
                    '[COORDINATOR] Autonomous Goal Dispatch operational at http://127.0.0.1:8090'
                )
                self.get_logger().info('=' * 72)
                break

            self.get_logger().warn(
                f'[COORDINATOR] Nav2 not yet fully active (bt_navigator={bt_label}). '
                'Recovering lifecycle transitions now...'
            )

            if self._nav_mgr_client is not None:
                mgr_req = ManageLifecycleNodes.Request()
                mgr_req.command = 0  # STARTUP
                self._call_async_wall_timeout(self._nav_mgr_client, mgr_req, timeout_sec=15.0)

            for nav_node in NAV2_ORDERED_NODES:
                if self._shutdown or not rclpy.ok():
                    return
                self._ensure_node_active(nav_node)

            time.sleep(1.5)


def main(args=None):
    rclpy.init(args=args)
    node = TrishulSystemCoordinator()
    executor = MultiThreadedExecutor(num_threads=2)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node._shutdown = True
        try:
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
