import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String # [추가] 데이터를 보내기 위한 문자열 메시지 타입
from cv_bridge import CvBridge
import cv2
import numpy as np
import message_filters
import os
from rclpy.qos import qos_profile_sensor_data 

class FaceTrackerNode(Node):
    def __init__(self):
        super().__init__('face_tracker_node')
        self.bridge = CvBridge()

        # 얼굴 인식 파일 로드
        xml_file = 'haarcascade_frontalface_default.xml'
        if not os.path.exists(xml_file):
            os.system(f'wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{xml_file}')
        self.face_cascade = cv2.CascadeClassifier(xml_file)

        # 1. [Subscribe] 카메라 데이터 받기
        # 사용자분이 확인해주신 정확한 토픽 주소
        color_topic = '/camera/camera/color/image_raw'
        depth_topic = '/camera/camera/aligned_depth_to_color/image_raw'

        self.get_logger().info(f"연결 시도 중: {color_topic}")
        
        # QoS 설정을 'sensor_data' (Best Effort)로 설정하여 호환성 확보
        color_sub = message_filters.Subscriber(self, Image, color_topic, qos_profile=qos_profile_sensor_data)
        depth_sub = message_filters.Subscriber(self, Image, depth_topic, qos_profile=qos_profile_sensor_data)

        self.ts = message_filters.ApproximateTimeSynchronizer([color_sub, depth_sub], 10, 0.3)
        self.ts.registerCallback(self.listener_callback)

        # 2. [Publish] 처리 결과 보내기 (New!)
        # '/face_info'라는 주제로 문자열(String) 데이터를 10개까지 큐에 담아 보냅니다.
        self.publisher_ = self.create_publisher(String, '/face_info', 10)
        self.get_logger().info("데이터 전송 준비 완료! 토픽명: /face_info")

    def listener_callback(self, color_msg, depth_msg):
        # print("데이터 수신 성공! 화면 갱신 중...", end='\r') 
        
        try:
            color_image = self.bridge.imgmsg_to_cv2(color_msg, "bgr8")
            depth_image = self.bridge.imgmsg_to_cv2(depth_msg, "16UC1")

            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

            face_detected = False

            for (x, y, w, h) in faces:
                face_detected = True
                center_x = x + w // 2
                center_y = y + h // 2
                
                # 화면 중심과의 오차 계산 (로봇 고개 돌리기 제어에 사용 가능)
                img_center_x = color_image.shape[1] // 2
                offset_x = center_x - img_center_x

                if 0 <= center_y < depth_image.shape[0] and 0 <= center_x < depth_image.shape[1]:
                #     
                    dist_m = depth_image[center_y, center_x] / 1000.0
                    # matrix in numpy has [height, width] mm to m
                    # 화면에 그리기
                    cv2.rectangle(color_image, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(color_image, f"{dist_m:.2f}m", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    # 3. [Publish] 결과 메시지 만들어서 보내기
                    msg = String()
                    msg.data = f"Target Detected! Dist: {dist_m:.2f}m, Offset: {offset_x}px"
                    self.publisher_.publish(msg)
                    
                    # 터미널에 로그 찍기 (보내고 있다는 확인)
                    # self.get_logger().info(f'Sending: "{msg.data}"')

            if not face_detected:
                # 얼굴이 없으면 없다고 보냄 (선택사항)
                pass

            cv2.imshow("Face Tracker", color_image)
            cv2.waitKey(1)
            
        except Exception as e:
            self.get_logger().error(f'Processing Error: {e}')

def main():
    rclpy.init()
    node = FaceTrackerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()

if __name__ == '__main__':
    main()