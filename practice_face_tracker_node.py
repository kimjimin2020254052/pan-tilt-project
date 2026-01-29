import rclpy
from rclpy.node import Node # Node in rclpy (ros client library for py)
from sensor_msgs.msg import Image # image standard
from std_msgs.msg import String
from cv_bridge import CvBridge
# ros message <-> OpenCV (python image)
import cv2 # imaging control (computer vision)
import numpy as np # image == Matrix in the computer. 
import message_filters # similar message can be combined.
import os # file check => wget, os.path.exists(...) => check the file

class FaceTrackerNode(Node):
    def __init__(self): # initial code
        super().__init__('face_tracker_node') # I can check in ros2 node list 
        # Node name.
        self.bridge = CvBridge() # self.bridge => all def can use bridge
        xml_file = 'haarcascade_frontalface_default.xml'
        # OpenCV face detection argorithm
        # if xml_file doesn't exist, you can download in the github
        if not os.path.exists(xml_file):
            os.system(f'wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{xml_file}')
        self.face_cascade = cv2.CascadeClassifier(xml_file)
        # self.face_cascasde => name of dectector

        color_sub = message_filters.Subscriber(self, Image, '/camera/camera/color/image_raw')
        # self => initial node. it can control subscriber
        # image => it can just see Image. other data is dismissed.
        # /camera/color/image_raw => topic name thar we need.
        depth_sub = message_filters.Subscriber(self, Image, '/camera/camera/aligned_depth_to_color/image_raw')
    
        self.ts = message_filters.ApproximateTimeSynchronizer([color_sub, depth_sub], 10, 0.3)
        self.ts.registerCallback(self.listener_callback)

        # 2. [Publish] 처리 결과 보내기 (New!)
        # '/face_info'라는 주제로 문자열(String) 데이터를 10개까지 큐에 담아 보냅니다.
        self.publisher_ = self.create_publisher(String, '/face_info', 10)
        self.get_logger().info("데이터 전송 준비 완료! 토픽명: /face_info")
    
    def listener_callback(self, color_msg, depth_msg):
        try:
            color_image = self.bridge.imgmsg_to_cv2(color_msg, "bgr8") 
            # bgr8 => normal image format
            depth_image = self.bridge.imgmsg_to_cv2(depth_msg, "16UC1")
            # 16UC1 : 16 bit channel for exact number
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            # use the face dector -> face_cascasde and function of detectMultiScale
            # because color data are heavy. So we can convert color image to black&white image(gray)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
            # if there are many faces. we can save all faces information.
            # like, faces = [[100,50,80,80],[320,120,90,90]] 
            face_detected = False

            for (x,y,w,h) in faces:
                face_detected = True
                center_x = x + w // 2  # x + width // 2 
                center_y = y + h // 2  # y + height // 2
                img_center_x = color_image.shape[1] // 2  # shape[0] -> height 
                                                        # shape[1] -> width
                                                        # shape[2] -> channels (Rgb)
                offset_x = center_x - img_center_x

                if 0 <= center_y < depth_image.shape[0] and 0 <= center_x < depth_image.shape[1]:  
                    # it just check the error that face disappear on the screen.
                    dist_m = depth_image[center_y, center_x] / 1000.0 # mm to m

                    cv2.circle(color_image, (center_x, center_y), w//2, (0, 255, 0), 2)
                    # (center, radius, rgb, thickness)
                    cv2.putText(color_image, f"{dist_m:.2f}m", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                    
                    # 3. [Publish] 결과 메시지 만들어서 보내기
                    msg = String()
                    # we can use msg format of the string 
                    msg.data = f"Target Detected! Dist: {dist_m:.2f}m, Offset: {offset_x}px"
                    # this is content.
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
    rclpy.init() # for using rclpy functions. Before starting,
    node = FaceTrackerNode() 
    try:
        rclpy.spin(node)  # continuous going
    except KeyboardInterrupt: # ctrl + c => stop
        pass

    finally:  
        node.destroy_node()  # node remove
        rclpy.shutdown()  # ros2 shutdown
        cv2.destroyAllWindows()  # camera window

if __name__ == '__main__':
    main()