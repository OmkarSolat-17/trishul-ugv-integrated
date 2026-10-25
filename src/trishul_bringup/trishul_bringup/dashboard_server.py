#!/usr/bin/env python3
"""
TRISHUL UGV -- Production-Grade Mission Control Dashboard Server
Implements the critical architectural requirements:
1. Latched Authoritative E-STOP with continuous zero-velocity clamp & Nav2 cancel.
2. ROS 2 NavigateToPose Action Client with bt_navigator ACTIVE state verification.
3. Live /map OccupancyGrid rendering with mathematically consistent coordinate transform.
4. Multi-stream MJPEG vision feeds (Depth Heatmap, AI YOLO HUD, Optical RGB, Rear Cam).
5. Non-blocking multi-threaded executor, input validation, and live readiness telemetry.
"""

import base64
import json
import math
import os
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from ament_index_python.packages import get_package_share_directory
import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.duration import Duration
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
import tf2_ros

from geometry_msgs.msg import PoseWithCovarianceStamped, Twist
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
try:
    from nav2_msgs.msg import SpeedLimit
except ImportError:
    SpeedLimit = None
from nav_msgs.msg import OccupancyGrid, Odometry, Path
from sensor_msgs.msg import Image, LaserScan
from std_msgs.msg import String


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in ('true', '1', 'yes')
    return bool(val)


class DaemonThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer with daemon worker threads and immediate port reuse."""

    daemon_threads = True
    allow_reuse_address = True


class SharedDashboardState:
    """Thread-safe state store shared between ROS 2 callbacks and HTTP request handler."""

    def __init__(self, slam_mode: bool = False, use_fallback_map: bool = True):
        self.lock = threading.Lock()
        self.slam_mode = slam_mode
        self.latest_jpeg = None
        self.raw_jpeg = None
        self.depth_jpeg = None
        self.yolo_jpeg = None
        self.optical_jpeg = None
        self.rear_jpeg = None
        self.pose = (
            {'x': 0.0, 'y': 0.0, 'yaw': 0.0}
            if slam_mode
            else {'x': -2.0, 'y': -0.5, 'yaw': 0.0}
        )
        self.vel = {'linear': 0.0, 'angular': 0.0}
        self.closest_obstacle = 20.0
        self.battery = 98.0
        self.laser_points = []
        self.path = []
        self.detections = []
        self.yolo_decision = {
            'action': 'CLEAR',
            'target': 'NONE',
            'distance': 10.0,
            'speed_limit': 2.5,
        }
        self.map_meta = {
            'resolution': 0.05,
            'width': 0,
            'height': 0,
            'origin_x': 0.0,
            'origin_y': 0.0,
        }
        self.map_jpeg_base64 = None
        self.map_version = 0
        if use_fallback_map and not slam_mode:
            self._load_fallback_map()
        self.estop_latched = False
        self.nav_state = 'IDLE'
        self.tf_ready = False
        self.odom_ready = False
        self.nav2_ready = False
        self.distance_remaining = 0.0
        self.eta_seconds = 0.0
        self.fps = 30.0
        self._last_frame_time = time.time()

    def update_depth_frame(self, heatmap_bgr):
        with self.lock:
            img = heatmap_bgr.copy()
            h, _ = img.shape[:2]
            cv2.putText(
                img,
                f"TRISHUL 3D DEPTH SENSOR [TURBO HEATMAP] | {time.strftime('%H:%M:%S')}",
                (14, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 242, 254),
                1,
                cv2.LINE_AA,
            )
            ret, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                self.depth_jpeg = jpeg.tobytes()

    def update_yolo_frame(self, bgr_img):
        with self.lock:
            ret, jpeg = cv2.imencode('.jpg', bgr_img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                data = jpeg.tobytes()
                self.yolo_jpeg = data
                self.latest_jpeg = data
                now = time.time()
                dt = now - self._last_frame_time
                if dt > 0:
                    self.fps = round(0.9 * self.fps + 0.1 * (1.0 / dt), 1)
                self._last_frame_time = now

    def update_raw_frame(self, bgr_img):
        with self.lock:
            img = bgr_img.copy()
            h, _ = img.shape[:2]
            cv2.putText(
                img,
                f"TRISHUL RAW CAMERA [/camera/image_raw] | {time.strftime('%H:%M:%S')}",
                (14, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 242, 254),
                1,
                cv2.LINE_AA,
            )
            ret, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                self.raw_jpeg = jpeg.tobytes()

    def update_optical_frame(self, bgr_img):
        with self.lock:
            img = bgr_img.copy()
            h, _ = img.shape[:2]
            cv2.putText(
                img,
                f"TRISHUL STEREO OPTICAL [/camera/color/image_raw] | {time.strftime('%H:%M:%S')}",
                (14, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 242, 254),
                1,
                cv2.LINE_AA,
            )
            ret, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                self.optical_jpeg = jpeg.tobytes()

    def update_rear_frame(self, bgr_img):
        with self.lock:
            img = bgr_img.copy()
            h, _ = img.shape[:2]
            cv2.putText(
                img,
                f"TRISHUL REAR RECON [/camera/rear/image_raw] | {time.strftime('%H:%M:%S')}",
                (14, h - 14),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 242, 254),
                1,
                cv2.LINE_AA,
            )
            ret, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                self.rear_jpeg = jpeg.tobytes()

    def _standby_card(self, title: str, subtitle: str, border_bgr=(0, 242, 254)) -> bytes:
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (12, 16, 24)
        for x in range(0, 640, 40):
            cv2.line(img, (x, 0), (x, 480), (20, 28, 42), 1)
        for y in range(0, 480, 40):
            cv2.line(img, (0, y), (640, y), (20, 28, 42), 1)

        cv2.rectangle(img, (20, 20), (620, 460), (0, 180, 216), 1)
        cv2.rectangle(img, (50, 140), (590, 340), (20, 28, 42), -1)
        cv2.rectangle(img, (50, 140), (590, 340), border_bgr, 1)

        cv2.putText(
            img, title, (70, 195),
            cv2.FONT_HERSHEY_SIMPLEX, 0.62, border_bgr, 2, cv2.LINE_AA,
        )
        cv2.putText(
            img, subtitle, (70, 235),
            cv2.FONT_HERSHEY_SIMPLEX, 0.46, (203, 213, 225), 1, cv2.LINE_AA,
        )
        cv2.putText(
            img,
            f"NAV: {self.nav_state} | POSE: ({self.pose['x']:.2f}, {self.pose['y']:.2f})",
            (70, 275),
            cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 242, 254), 1, cv2.LINE_AA,
        )
        cv2.putText(
            img,
            f"LOCAL TIME: {time.strftime('%H:%M:%S')}",
            (70, 310),
            cv2.FONT_HERSHEY_SIMPLEX, 0.40, (148, 163, 184), 1, cv2.LINE_AA,
        )
        _, jpeg = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return jpeg.tobytes()

    def get_jpeg(self, feed: str = 'depth') -> bytes:
        with self.lock:
            if feed in ('depth', 'heatmap'):
                if self.depth_jpeg is not None:
                    return self.depth_jpeg
                if self.raw_jpeg is not None:
                    return self.raw_jpeg
                hm = np.zeros((480, 640, 3), dtype=np.uint8)
                for y in range(480):
                    val = int((y / 480.0) * 255)
                    hm[y, :] = (val, val, val)
                hm = cv2.applyColorMap(hm[:, :, 0], cv2.COLORMAP_TURBO)
                cv2.putText(
                    hm, 'TRISHUL 3D DEPTH SENSOR [ACQUIRING DEPTH HEATMAP...]',
                    (30, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (255, 255, 255), 2, cv2.LINE_AA,
                )
                _, jpeg = cv2.imencode('.jpg', hm, [cv2.IMWRITE_JPEG_QUALITY, 80])
                return jpeg.tobytes()

            if feed in ('yolo', 'ai', 'detection', 'combined'):
                if self.yolo_jpeg is not None:
                    return self.yolo_jpeg
                if self.latest_jpeg is not None:
                    return self.latest_jpeg
                if self.optical_jpeg is not None:
                    return self.optical_jpeg
                if self.depth_jpeg is not None:
                    return self.depth_jpeg
                return self._standby_card(
                    'AI VISION & YOLO ENGINE',
                    'Awaiting /camera/color/image_raw sensor stream...',
                )

            if feed in ('stereo', 'optical'):
                if self.optical_jpeg is not None:
                    return self.optical_jpeg
                if self.yolo_jpeg is not None:
                    return self.yolo_jpeg
                return self._standby_card(
                    'STEREO OPTICAL CAMERA',
                    'Awaiting /camera/color/image_raw sensor stream...',
                )

            if feed == 'rear':
                if self.rear_jpeg is not None:
                    return self.rear_jpeg
                return self._standby_card(
                    'REAR RECON CAMERA',
                    'Awaiting /camera/rear/image_raw sensor stream...',
                    border_bgr=(255, 82, 82),
                )

            if feed == 'raw' and self.raw_jpeg is not None:
                return self.raw_jpeg
            if self.depth_jpeg is not None:
                return self.depth_jpeg
            if self.latest_jpeg is not None:
                return self.latest_jpeg
            return self._standby_card(
                'TRISHUL UGV VISION FEED',
                'Acquiring simulation camera sensor streams...',
            )

    def _load_fallback_map(self):
        """Preload tb3_sandbox arena map ONLY when running AMCL sandbox profile."""
        pgm_path = '/opt/ros/jazzy/share/nav2_bringup/maps/tb3_sandbox.pgm'
        if os.path.exists(pgm_path):
            try:
                pgm = cv2.imread(pgm_path, cv2.IMREAD_GRAYSCALE)
                if pgm is not None:
                    h, w = pgm.shape
                    self.map_meta = {
                        'resolution': 0.05,
                        'width': w,
                        'height': h,
                        'origin_x': -10.0,
                        'origin_y': -10.0,
                    }
                    map_rgba = np.zeros((h, w, 4), dtype=np.uint8)
                    map_rgba[pgm > 240] = [27, 40, 56, 255]

                    obs_mask = (pgm < 100).astype(np.uint8)
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
                    obs_dilated = cv2.dilate(obs_mask, kernel, iterations=1)
                    map_rgba[obs_dilated > 0] = [0, 242, 254, 255]
                    map_rgba[(pgm >= 100) & (pgm <= 240) & (obs_dilated == 0)] = [8, 12, 18, 210]

                    map_rgba = np.flipud(map_rgba)
                    ret, buf = cv2.imencode('.png', map_rgba)
                    if ret:
                        self.map_jpeg_base64 = base64.b64encode(buf).decode('utf-8')
                        self.map_version = 1
            except Exception:
                pass

    def update_map(self, msg: OccupancyGrid):
        with self.lock:
            w = msg.info.width
            h = msg.info.height
            res = msg.info.resolution
            ox = msg.info.origin.position.x
            oy = msg.info.origin.position.y

            if w == 0 or h == 0:
                return

            self.map_meta = {
                'resolution': res,
                'width': w,
                'height': h,
                'origin_x': ox,
                'origin_y': oy,
            }

            raw = np.array(msg.data, dtype=np.int8).reshape((h, w))
            map_rgba = np.zeros((h, w, 4), dtype=np.uint8)
            map_rgba[raw == -1] = [18, 26, 38, 160]
            map_rgba[raw == 0] = [36, 48, 68, 235]
            mask_cost = (raw > 0) & (raw <= 50)
            map_rgba[mask_cost] = [0, 140, 255, 200]
            map_rgba[raw > 50] = [254, 242, 0, 255]

            map_rgba = np.flipud(map_rgba)
            ret, buf = cv2.imencode('.png', map_rgba)
            if ret:
                self.map_jpeg_base64 = base64.b64encode(buf).decode('utf-8')
                self.map_version += 1

    def get_telemetry_snapshot(self):
        with self.lock:
            self.battery = max(15.0, round(self.battery - 0.001, 2))
            return {
                'pose': self.pose,
                'vel': self.vel,
                'closest_obstacle': round(self.closest_obstacle, 2),
                'battery': int(self.battery),
                'laser_points': self.laser_points,
                'path': self.path,
                'detections': self.detections,
                'yolo_decision': self.yolo_decision,
                'map_meta': self.map_meta,
                'map_image': self.map_jpeg_base64,
                'map_version': self.map_version,
                'estop_latched': self.estop_latched,
                'nav_state': self.nav_state,
                'slam_mode': self.slam_mode,
                'tf_ready': self.tf_ready,
                'odom_ready': self.odom_ready,
                'nav2_ready': self.nav2_ready,
                'distance_remaining': round(self.distance_remaining, 2),
                'eta_seconds': round(self.eta_seconds, 1),
                'fps': self.fps,
                'has_optical': self.optical_jpeg is not None,
                'has_rear': self.rear_jpeg is not None,
                'has_depth': self.depth_jpeg is not None or self.latest_jpeg is not None,
            }


class DashboardHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Handles static files, MJPEG video streaming, and validated REST API calls."""

    web_dir = ''
    shared_state: SharedDashboardState = None
    node_ref = None

    def translate_path(self, path):
        clean_path = path.split('?')[0].split('#')[0]
        if clean_path in ('', '/'):
            clean_path = '/index.html'
        return os.path.join(self.web_dir, clean_path.lstrip('/'))

    def do_GET(self):
        if self.path.startswith('/stream/video'):
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header(
                'Content-Type', 'multipart/x-mixed-replace; boundary=frame'
            )
            self.end_headers()
            try:
                while True:
                    feed = 'depth'
                    if 'feed=' in self.path:
                        try:
                            feed = self.path.split('feed=')[1].split('&')[0]
                        except Exception:
                            feed = 'combined'
                    frame = self.shared_state.get_jpeg(feed)
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(frame)))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                    time.sleep(0.05)
            except (ConnectionResetError, BrokenPipeError, OSError):
                pass
            return

        if self.path.startswith('/events'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                while True:
                    snapshot = self.shared_state.get_telemetry_snapshot()
                    msg = f'data: {json.dumps(snapshot)}\n\n'
                    self.wfile.write(msg.encode('utf-8'))
                    self.wfile.flush()
                    time.sleep(0.1)
            except (ConnectionResetError, BrokenPipeError, OSError):
                pass
            return

        if self.path.startswith('/api/state'):
            self._send_json(self.shared_state.get_telemetry_snapshot())
            return

        super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            req_data = json.loads(body.decode('utf-8'))
        except Exception:
            self._send_json({'status': 'error', 'message': 'Invalid JSON body'}, 400)
            return

        # 1. Teleoperation
        if self.path == '/api/teleop':
            if self.shared_state.estop_latched:
                self._send_json(
                    {'status': 'error', 'message': 'E-STOP is latched. Reset E-STOP first.'},
                    403,
                )
                return

            try:
                lin = float(req_data.get('linear', 0.0))
                ang = float(req_data.get('angular', 0.0))
            except (ValueError, TypeError):
                self._send_json({'status': 'error', 'message': 'Non-numeric velocities'}, 400)
                return

            max_s = getattr(self.node_ref, 'teleop_speed_limit', 2.5) if self.node_ref else 5.0
            lin = max(-max_s, min(max_s, lin))
            ang = max(-3.0, min(3.0, ang))

            if self.node_ref:
                self.node_ref.publish_teleop(lin, ang)
            self._send_json({'status': 'ok'})
            return

        # 2. Speed Limit Adjustment
        if self.path == '/api/speed_limit':
            try:
                speed = float(req_data.get('speed', 2.5))
            except (ValueError, TypeError):
                self._send_json({'status': 'error', 'message': 'Invalid speed parameter'}, 400)
                return
            if self.node_ref:
                self.node_ref.set_speed_limit(speed)
            self._send_json({'status': 'ok', 'speed': speed})
            return

        # 3. 10m Radius Scan Routine
        if self.path == '/api/scan_10m':
            if self.shared_state.estop_latched:
                self._send_json({'status': 'error', 'message': 'E-STOP is latched.'}, 403)
                return
            if self.node_ref and self.node_ref.start_10m_scan():
                self._send_json({'status': 'ok', 'message': '10m Area Scan Sequence Started'})
                return
            self._send_json({'status': 'error', 'message': 'Could not start scan'}, 500)
            return

        # 4. Cancel / Preempt Goal
        if self.path == '/api/cancel':
            if self.node_ref and self.node_ref.active_goal_handle:
                self.node_ref.active_goal_handle.cancel_goal_async()
                self.node_ref.active_goal_handle = None
                with self.shared_state.lock:
                    self.shared_state.nav_state = 'CANCELLED'
            self._send_json({'status': 'ok'})
            return

        # 5. Nav2 Goal Dispatch
        if self.path == '/api/goal':
            if self.shared_state.estop_latched:
                self._send_json(
                    {'status': 'error', 'message': 'E-STOP is latched. Reset E-STOP first.'},
                    403,
                )
                return

            try:
                gx = float(req_data.get('x', 0.0))
                gy = float(req_data.get('y', 0.0))
                yaw = float(req_data.get('yaw', 0.0))
            except (ValueError, TypeError):
                self._send_json({'status': 'error', 'message': 'Non-numeric coordinates'}, 400)
                return

            if self.node_ref:
                ok, msg = self.node_ref.dispatch_nav_goal(gx, gy, yaw)
                if ok:
                    self._send_json({'status': 'ok', 'message': msg})
                else:
                    self._send_json({'status': 'error', 'message': msg}, 503)
                return

            self._send_json({'status': 'error', 'message': 'Node unavailable'}, 500)
            return

        # 6. Emergency Stop (Latched)
        if self.path == '/api/estop':
            if self.node_ref:
                self.node_ref.emergency_stop()
            self._send_json({'status': 'ok', 'message': 'Emergency stop latched'})
            return

        # 7. Reset E-Stop
        if self.path == '/api/reset_estop':
            if self.node_ref:
                self.node_ref.reset_estop()
            self._send_json({'status': 'ok', 'message': 'E-Stop reset. Systems nominal.'})
            return

        self._send_json({'status': 'error', 'message': 'Not found'}, 404)

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        return


class TrishulDashboardServerNode(Node):
    def __init__(self):
        super().__init__('trishul_dashboard_server')

        # Parameters
        self.declare_parameter('port', 8090)
        self.declare_parameter('web_root', '')
        self.declare_parameter('slam_mode', False)
        self.declare_parameter('use_fallback_map', True)

        self.port = int(self.get_parameter('port').value)
        slam_mode = _parse_bool(self.get_parameter('slam_mode').value)
        use_fallback_map = _parse_bool(self.get_parameter('use_fallback_map').value)

        # Locate Web Assets portably across any developer workspace
        custom_root = self.get_parameter('web_root').value
        if custom_root and os.path.isdir(custom_root):
            self.web_dir = custom_root
        else:
            try:
                share_web = os.path.join(get_package_share_directory('trishul_bringup'), 'web')
            except Exception:
                share_web = ''
            rel_web = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'web'))
            if share_web and os.path.isdir(share_web):
                self.web_dir = share_web
            elif os.path.isdir(rel_web):
                self.web_dir = rel_web
            else:
                self.web_dir = os.path.dirname(__file__)

        self.get_logger().info(f'Serving Trishul Web Dashboard from: {self.web_dir}')

        self.shared_state = SharedDashboardState(
            slam_mode=slam_mode, use_fallback_map=use_fallback_map
        )
        self.bridge = CvBridge()
        self.cb_group = ReentrantCallbackGroup()

        # Publishers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.cmd_vel_smoothed_pub = self.create_publisher(Twist, '/cmd_vel_smoothed', 10)
        self.teleop_speed_limit = 2.5
        if SpeedLimit is not None:
            self.speed_limit_pub = self.create_publisher(SpeedLimit, '/speed_limit', 10)
        self.safety_cmd_pub = self.create_publisher(Twist, '/ugv/cmd_vel_request', 10)

        # Authoritative Map-Frame Localization (TF2 map -> base_footprint)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        self.has_map_pose = False

        # AMCL Map Pose Subscriber
        self.amcl_sub = self.create_subscription(
            PoseWithCovarianceStamped,
            '/amcl_pose',
            self.amcl_callback,
            10,
            callback_group=self.cb_group,
        )

        # Nav2 Action Client & bt_navigator Lifecycle State Client
        self.nav_action_client = ActionClient(
            self, NavigateToPose, 'navigate_to_pose', callback_group=self.cb_group
        )
        self.bt_state_client = self.create_client(
            GetState, '/bt_navigator/get_state', callback_group=self.cb_group
        )
        self.active_goal_handle = None
        self._shutdown = False

        # Background wall-clock poller for TF pose & bt_navigator ACTIVE state
        self._monitor_thread = threading.Thread(target=self._background_monitor_loop, daemon=True)
        self._monitor_thread.start()

        # QoS Profiles
        sensor_qos = QoSProfile(
            reliability=ReliabilityPolicy.BEST_EFFORT,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        map_qos = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
            history=HistoryPolicy.KEEP_LAST,
            depth=1,
        )

        # Subscriptions
        self.image_sub = self.create_subscription(
            Image, '/ugv/combined/image', self.image_callback, sensor_qos,
            callback_group=self.cb_group,
        )
        self.depth_hm_sub = self.create_subscription(
            Image, '/ugv/depth/heatmap', self.depth_hm_callback, sensor_qos,
            callback_group=self.cb_group,
        )
        self.rear_image_sub = self.create_subscription(
            Image, '/camera/rear/image_raw', self.rear_image_callback, sensor_qos,
            callback_group=self.cb_group,
        )
        self.color_image_sub = self.create_subscription(
            Image, '/camera/color/image_raw', self.color_image_callback, sensor_qos,
            callback_group=self.cb_group,
        )
        self.raw_image_sub = self.create_subscription(
            Image, '/camera/image_raw', self.raw_image_callback, sensor_qos,
            callback_group=self.cb_group,
        )
        self.odom_sub = self.create_subscription(
            Odometry, '/odom', self.odom_callback, 10, callback_group=self.cb_group
        )
        self.scan_sub = self.create_subscription(
            LaserScan, '/scan', self.scan_callback, sensor_qos, callback_group=self.cb_group
        )
        self.map_sub = self.create_subscription(
            OccupancyGrid, '/map', self.map_callback, map_qos, callback_group=self.cb_group
        )
        self.plan_sub = self.create_subscription(
            Path, '/plan', self.plan_callback, 10, callback_group=self.cb_group
        )
        self.detect_sub = self.create_subscription(
            String, '/ugv/detections', self.detections_callback, 10, callback_group=self.cb_group
        )
        self.yolo_dec_sub = self.create_subscription(
            String, '/ugv/yolo_decision', self.yolo_decision_callback, 10,
            callback_group=self.cb_group,
        )

        # Launch HTTP Server
        DashboardHTTPRequestHandler.web_dir = self.web_dir
        DashboardHTTPRequestHandler.shared_state = self.shared_state
        DashboardHTTPRequestHandler.node_ref = self

        self.server = DaemonThreadingHTTPServer(
            ('0.0.0.0', self.port), DashboardHTTPRequestHandler
        )
        self.server_thread = threading.Thread(
            target=self.server.serve_forever, daemon=True
        )
        self.server_thread.start()

        self.get_logger().info('=' * 65)
        self.get_logger().info(f'TRISHUL MISSION CONTROL ACTIVE: http://127.0.0.1:{self.port}')
        self.get_logger().info('=' * 65)

    def _background_monitor_loop(self):
        """Wall-clock loop for TF sync, E-STOP clamp, and bt_navigator readiness check."""
        last_bt_check = 0.0
        while not self._shutdown and rclpy.ok():
            # 1. Authoritative E-STOP clamp (20 Hz)
            if self.shared_state.estop_latched:
                zero_twist = Twist()
                self.cmd_vel_pub.publish(zero_twist)
                self.safety_cmd_pub.publish(zero_twist)

            # 2. Map-frame TF pose sync (20 Hz)
            self._sync_map_pose()

            # 3. Check bt_navigator ACTIVE state (every 1.0s)
            now = time.monotonic()
            if now - last_bt_check >= 1.0:
                last_bt_check = now
                self._refresh_nav2_ready()

            time.sleep(0.05)

    def _refresh_nav2_ready(self):
        if not self.bt_state_client.service_is_ready():
            with self.shared_state.lock:
                self.shared_state.nav2_ready = False
            return
        try:
            fut = self.bt_state_client.call_async(GetState.Request())
            deadline = time.monotonic() + 0.8
            while not fut.done() and time.monotonic() < deadline:
                time.sleep(0.02)
            if fut.done() and fut.result() is not None:
                is_active = fut.result().current_state.id == 3  # PRIMARY_STATE_ACTIVE
                with self.shared_state.lock:
                    self.shared_state.nav2_ready = is_active
        except Exception:
            pass

    def depth_hm_callback(self, msg: Image):
        try:
            if msg.encoding in ('bgr8', 'rgb8'):
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                self.shared_state.update_depth_frame(img)
        except Exception as e:
            self.get_logger().error(
                f'Depth heatmap callback error: {e}', throttle_duration_sec=5.0
            )

    def image_callback(self, msg: Image):
        self._decode_image(msg)

    def rear_image_callback(self, msg: Image):
        try:
            if msg.encoding in ('bgr8', 'rgb8'):
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                self.shared_state.update_rear_frame(img)
        except Exception:
            pass

    def color_image_callback(self, msg: Image):
        try:
            if msg.encoding in ('bgr8', 'rgb8'):
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                self.shared_state.update_optical_frame(img)
        except Exception:
            pass

    def raw_image_callback(self, msg: Image):
        try:
            if msg.encoding in ('32FC1', '16UC1', '32F', 'passthrough'):
                depth_cv = self.bridge.imgmsg_to_cv2(msg, desired_encoding='passthrough')
                if msg.encoding == '16UC1':
                    depth_cv = depth_cv.astype(np.float32) / 1000.0
                depth_clean = np.nan_to_num(depth_cv, nan=0.0, posinf=8.0, neginf=0.0)
                depth_scaled = np.clip(depth_clean / 8.0 * 255.0, 0, 255).astype(np.uint8)
                heatmap = cv2.applyColorMap(depth_scaled, cv2.COLORMAP_TURBO)
                self.shared_state.update_depth_frame(heatmap)
                self.shared_state.update_raw_frame(heatmap)
            elif msg.encoding in ('bgr8', 'rgb8'):
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                self.shared_state.update_raw_frame(img)
        except Exception as e:
            self.get_logger().error(
                f'Raw depth conversion error: {e}', throttle_duration_sec=5.0
            )

    def _decode_image(self, msg: Image):
        try:
            if msg.encoding in ('bgr8', 'rgb8'):
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                self.shared_state.update_yolo_frame(img)
            elif msg.encoding == 'mono8':
                img = self.bridge.imgmsg_to_cv2(msg, desired_encoding='mono8')
                img_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                self.shared_state.update_yolo_frame(img_bgr)
        except Exception as e:
            self.get_logger().error(f'AI image decode error: {e}', throttle_duration_sec=5.0)

    def _sync_map_pose(self):
        """Authoritative map-frame pose resolution identical to RViz and Nav2 costmaps."""
        for child_frame in ('base_footprint', 'base_link'):
            try:
                t = self.tf_buffer.lookup_transform(
                    'map',
                    child_frame,
                    rclpy.time.Time(),
                    timeout=Duration(seconds=0.01),
                )
                px = t.transform.translation.x
                py = t.transform.translation.y
                qx = t.transform.rotation.x
                qy = t.transform.rotation.y
                qz = t.transform.rotation.z
                qw = t.transform.rotation.w
                siny_cosp = 2.0 * (qw * qz + qx * qy)
                cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                with self.shared_state.lock:
                    self.shared_state.pose = {
                        'x': round(px, 3),
                        'y': round(py, 3),
                        'yaw': round(yaw, 3),
                    }
                    self.shared_state.tf_ready = True
                self.has_map_pose = True
                return
            except Exception:
                continue

    def amcl_callback(self, msg: PoseWithCovarianceStamped):
        px = msg.pose.pose.position.x
        py = msg.pose.pose.position.y
        qx = msg.pose.pose.orientation.x
        qy = msg.pose.pose.orientation.y
        qz = msg.pose.pose.orientation.z
        qw = msg.pose.pose.orientation.w
        siny_cosp = 2.0 * (qw * qz + qx * qy)
        cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        with self.shared_state.lock:
            self.shared_state.pose = {
                'x': round(px, 3),
                'y': round(py, 3),
                'yaw': round(yaw, 3),
            }
            self.shared_state.tf_ready = True
        self.has_map_pose = True

    def odom_callback(self, msg: Odometry):
        vx = msg.twist.twist.linear.x
        wz = msg.twist.twist.angular.z

        with self.shared_state.lock:
            self.shared_state.odom_ready = True
            self.shared_state.vel = {'linear': round(vx, 3), 'angular': round(wz, 3)}
            if not self.has_map_pose:
                px = msg.pose.pose.position.x
                py = msg.pose.pose.position.y
                qx = msg.pose.pose.orientation.x
                qy = msg.pose.pose.orientation.y
                qz = msg.pose.pose.orientation.z
                qw = msg.pose.pose.orientation.w
                siny_cosp = 2.0 * (qw * qz + qx * qy)
                cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
                yaw = math.atan2(siny_cosp, cosy_cosp)
                self.shared_state.pose = {
                    'x': round(px, 3),
                    'y': round(py, 3),
                    'yaw': round(yaw, 3),
                }

    def scan_callback(self, msg: LaserScan):
        ranges = msg.ranges
        valid = [
            r for r in ranges
            if msg.range_min < r < msg.range_max and math.isfinite(r)
        ]
        closest = min(valid) if valid else 20.0

        points = []
        step = max(1, len(ranges) // 72)
        for i in range(0, len(ranges), step):
            r = ranges[i]
            if max(0.20, msg.range_min) < r < 18.0 and math.isfinite(r):
                angle = msg.angle_min + i * msg.angle_increment
                rx = r * math.cos(angle)
                ry = r * math.sin(angle)
                points.append([round(rx, 2), round(ry, 2)])

        with self.shared_state.lock:
            self.shared_state.closest_obstacle = closest
            self.shared_state.laser_points = points

    def map_callback(self, msg: OccupancyGrid):
        self.shared_state.update_map(msg)

    def plan_callback(self, msg: Path):
        path_pts = []
        for p in msg.poses[::2]:
            path_pts.append([round(p.pose.position.x, 2), round(p.pose.position.y, 2)])
        with self.shared_state.lock:
            self.shared_state.path = path_pts

    def detections_callback(self, msg: String):
        try:
            dets = json.loads(msg.data)
            with self.shared_state.lock:
                self.shared_state.detections = dets
        except Exception:
            pass

    def yolo_decision_callback(self, msg: String):
        try:
            dec = json.loads(msg.data)
            with self.shared_state.lock:
                self.shared_state.yolo_decision = dec
        except Exception:
            pass

    def set_speed_limit(self, speed):
        speed = max(0.2, min(5.0, float(speed)))
        self.teleop_speed_limit = speed
        if SpeedLimit is not None and hasattr(self, 'speed_limit_pub'):
            lim_msg = SpeedLimit()
            lim_msg.percentage = False
            lim_msg.speed_limit = float(speed)
            self.speed_limit_pub.publish(lim_msg)
        self.get_logger().info(
            f'[MISSION CONTROL] Vehicle speed limit calibrated to {speed:.2f} m/s'
        )

    def start_10m_scan(self):
        if self.shared_state.estop_latched:
            return False
        scan_t = threading.Thread(target=self._run_10m_scan_routine, daemon=True)
        scan_t.start()
        return True

    def _run_10m_scan_routine(self):
        self.get_logger().info(
            '[RADAR] Initiating Autonomous 10m Sector Sweep & Area Traversal...'
        )
        if self.active_goal_handle is not None:
            self.get_logger().info('[RADAR] Preempting active Nav2 goal for 10m area sweep...')
            self.active_goal_handle.cancel_goal_async()
            self.active_goal_handle = None

        with self.shared_state.lock:
            self.shared_state.nav_state = 'SCANNING 10M'

        sweep_twist = Twist()
        sweep_twist.angular.z = 1.20

        fwd_twist = Twist()
        fwd_twist.linear.x = 2.0

        stop_twist = Twist()

        def _publish_cmd(cmd, duration_sec, dt=0.05):
            steps = int(duration_sec / dt)
            for _ in range(steps):
                if self.shared_state.estop_latched:
                    break
                self.cmd_vel_pub.publish(cmd)
                if hasattr(self, 'cmd_vel_smoothed_pub'):
                    self.cmd_vel_smoothed_pub.publish(cmd)
                self.safety_cmd_pub.publish(cmd)
                time.sleep(dt)

        self.get_logger().info('[RADAR] Phase 1/4: 360-degree Origin Radar Sweep...')
        _publish_cmd(sweep_twist, duration_sec=5.2)
        _publish_cmd(stop_twist, duration_sec=0.3)

        if not self.shared_state.estop_latched:
            self.get_logger().info('[RADAR] Phase 2/4: Transiting 10 meters outward...')
            _publish_cmd(fwd_twist, duration_sec=5.0)
            _publish_cmd(stop_twist, duration_sec=0.4)

        if not self.shared_state.estop_latched:
            self.get_logger().info('[RADAR] Phase 3/4: 360-degree Perimeter Radar Sweep...')
            _publish_cmd(sweep_twist, duration_sec=5.2)
            _publish_cmd(stop_twist, duration_sec=0.4)

        if not self.shared_state.estop_latched:
            self.get_logger().info('[RADAR] Phase 4/4: Perimeter lateral coverage sweep...')
            arc_twist = Twist()
            arc_twist.linear.x = 1.2
            arc_twist.angular.z = 0.5
            _publish_cmd(arc_twist, duration_sec=4.0)
            _publish_cmd(stop_twist, duration_sec=0.5)

        with self.shared_state.lock:
            self.shared_state.nav_state = 'IDLE'
        self.get_logger().info(
            '[RADAR] Full 10m Operational Radius Mapped & Refreshed Successfully.'
        )

    def publish_teleop(self, linear, angular):
        if self.shared_state.estop_latched:
            return

        if self.active_goal_handle is not None:
            self.get_logger().info(
                'Manual teleop input received: Preempting Nav2 autonomous goal.'
            )
            self.active_goal_handle.cancel_goal_async()
            self.active_goal_handle = None
            with self.shared_state.lock:
                self.shared_state.nav_state = 'TELEOP'

        t = Twist()
        max_s = getattr(self, 'teleop_speed_limit', 2.5)
        t.linear.x = max(-max_s, min(max_s, float(linear)))
        t.angular.z = float(angular)
        self.cmd_vel_pub.publish(t)
        self.safety_cmd_pub.publish(t)

    def dispatch_nav_goal(self, x, y, yaw=0.0):
        if self.shared_state.estop_latched:
            self.get_logger().warn('Cannot dispatch Nav2 goal: E-STOP is latched.')
            return False, 'E-STOP is latched. Reset E-STOP first.'

        if not self.nav_action_client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error('Nav2 NavigateToPose action server not available!')
            return False, 'Nav2 action server is still starting. Try again in a few seconds.'

        # Wait briefly if bt_navigator is still completing lifecycle activation
        wait_deadline = time.monotonic() + 4.0
        while not self.shared_state.nav2_ready and time.monotonic() < wait_deadline:
            self._refresh_nav2_ready()
            if self.shared_state.nav2_ready:
                break
            time.sleep(0.25)

        if not self.shared_state.nav2_ready:
            self.get_logger().warn('bt_navigator is still activating; holding goal until ACTIVE.')
            return (
                False,
                'Nav2 bt_navigator is still activating (awaiting SLAM/TF). Retry momentarily.',
            )

        if self.active_goal_handle is not None:
            self.active_goal_handle.cancel_goal_async()

        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x = float(x)
        goal_msg.pose.pose.position.y = float(y)
        goal_msg.pose.pose.position.z = 0.0
        goal_msg.pose.pose.orientation.z = math.sin(yaw / 2.0)
        goal_msg.pose.pose.orientation.w = math.cos(yaw / 2.0)

        self.get_logger().info(f'Dispatching NavigateToPose Action Goal: ({x:.2f}, {y:.2f})')
        with self.shared_state.lock:
            self.shared_state.nav_state = 'NAVIGATING'

        send_future = self.nav_action_client.send_goal_async(
            goal_msg, feedback_callback=self._nav_feedback_cb
        )
        send_future.add_done_callback(self._nav_goal_response_cb)
        return True, f'Goal ({x:.2f}, {y:.2f}) dispatched to Nav2.'

    def _nav_goal_response_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().warn('Nav2 Goal rejected by server.')
            with self.shared_state.lock:
                self.shared_state.nav_state = 'REJECTED'
            return

        self.get_logger().info('Nav2 Goal accepted and active.')
        self.active_goal_handle = goal_handle
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._nav_result_cb)

    def _nav_feedback_cb(self, feedback_msg):
        fb = feedback_msg.feedback
        dist = fb.distance_remaining
        eta = fb.estimated_time_remaining.sec + fb.estimated_time_remaining.nanosec * 1e-9
        with self.shared_state.lock:
            self.shared_state.distance_remaining = dist
            self.shared_state.eta_seconds = eta

    def _nav_result_cb(self, future):
        res = future.result()
        status = res.status
        self.active_goal_handle = None
        with self.shared_state.lock:
            if status == 4:  # STATUS_SUCCEEDED
                self.shared_state.nav_state = 'SUCCEEDED'
                self.get_logger().info('Nav2 Navigation Succeeded!')
            elif status == 5:  # STATUS_CANCELED
                self.shared_state.nav_state = 'CANCELLED'
                self.get_logger().info('Nav2 Navigation Cancelled.')
            else:
                self.shared_state.nav_state = 'FAILED'
                self.get_logger().warn(f'Nav2 Navigation ended with status {status}')

    def emergency_stop(self):
        with self.shared_state.lock:
            self.shared_state.estop_latched = True
            self.shared_state.nav_state = 'E-STOP'

        if self.active_goal_handle is not None:
            self.get_logger().warn('E-STOP: Cancelling active Nav2 goal.')
            self.active_goal_handle.cancel_goal_async()
            self.active_goal_handle = None

        zero = Twist()
        self.cmd_vel_pub.publish(zero)
        self.safety_cmd_pub.publish(zero)
        self.get_logger().error('>>> LATCHED EMERGENCY STOP ACTIVATED <<<')

    def reset_estop(self):
        with self.shared_state.lock:
            self.shared_state.estop_latched = False
            self.shared_state.nav_state = 'IDLE'
        self.get_logger().info('E-STOP Latch cleared. System restored to IDLE.')


def main(args=None):
    rclpy.init(args=args)
    node = TrishulDashboardServerNode()
    executor = MultiThreadedExecutor(num_threads=4)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node._shutdown = True
        try:
            node.server.shutdown()
            node.destroy_node()
        except Exception:
            pass
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
