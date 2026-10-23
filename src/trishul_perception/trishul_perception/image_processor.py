import os
import json
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge

try:
    from ultralytics import YOLO
    import torch
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from ament_index_python.packages import get_package_share_directory


class ImageProcessor(Node):
    def __init__(self):
        super().__init__('image_processor')

        pkg_dir = get_package_share_directory('trishul_perception')
        default_model = os.path.join(pkg_dir, 'models', 'yolo26n.pt')

        self.declare_parameter('model_path', default_model)
        self.declare_parameter('confidence', 0.35)
        self.declare_parameter('input_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/ugv/combined/image')
        self.declare_parameter('detections_topic', '/ugv/detections')

        model_path = self.get_parameter('model_path').value
        self.confidence = float(self.get_parameter('confidence').value)
        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        detections_topic = self.get_parameter('detections_topic').value

        self.bridge = CvBridge()
        self.model = None

        if ULTRALYTICS_AVAILABLE:
            if os.path.exists(model_path):
                self.device = 0 if torch.cuda.is_available() else 'cpu'
                self.get_logger().info(f'Loading YOLO model from {model_path} on device {self.device}')
                self.model = YOLO(model_path)
            else:
                self.get_logger().error(f'Model file not found at: {model_path}')
        else:
            self.get_logger().warning(
                'Ultralytics is not installed in the current Python environment. '
                'Image pass-through mode active.'
            )

        self.subscription = self.create_subscription(
            Image, input_topic, self.image_callback, 10
        )
        self.image_pub = self.create_publisher(Image, output_topic, 10)
        self.det_pub = self.create_publisher(String, detections_topic, 10)

        self.get_logger().info(
            f'Trishul Perception Node initialized. In: {input_topic} -> Out: {output_topic}'
        )

    def image_callback(self, msg):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            detections_list = []

            if self.model is not None:
                results = self.model.predict(
                    source=frame,
                    imgsz=640,
                    conf=self.confidence,
                    device=self.device,
                    verbose=False
                )
                boxes = results[0].boxes
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    name = self.model.names[class_id]
                    detections_list.append({'class': name, 'confidence': round(conf, 3)})

                annotated = results[0].plot()
                out_msg = self.bridge.cv2_to_imgmsg(annotated, encoding='bgr8')
            else:
                out_msg = self.bridge.cv2_to_imgmsg(frame, encoding='bgr8')

            out_msg.header = msg.header
            self.image_pub.publish(out_msg)

            det_msg = String()
            det_msg.data = json.dumps(detections_list)
            self.det_pub.publish(det_msg)

        except Exception as e:
            self.get_logger().error(f'Image processing error: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = ImageProcessor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
