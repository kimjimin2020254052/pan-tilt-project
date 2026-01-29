import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
import message_filters
import os
import socket

class MotorTrackerNode(Node):
    def __init__ (self) :
        super().__init__('Motor_track_node')
        self.bridge = CvBridge()

        xml_file = 'haarcascade_frontalface_default.xml'
        if not os.path.exists(xml_file):
            os.system(f'wget https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/{xml_file}')
        self.face_cascade = cv2.CascadeClassifier(xml_file)

        # Subscriber
        color_sub = message_filters.Subscriber(self, Image, '/camera/camera/color/image_raw')
        depth_sub = message_filters.Subscriber(self, Image, '/camera/camera/aligned_depth_to_color/image_raw')

        self.ts = message_filters.ApproximateTimeSynchronizer([color_sub, depth_sub], 10, 0.3)
        self.ts.registerCallback(self.listener_callback)

        # Publisher => we try to publish points information. 
        #self.publisher_ = self.create_publisher(Point, 'point_info', 10)
        #self.get_logger().info("Ready to publish! topic name : /point_info")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rpi_address = ('192.168.0.221', 5005)
        self.get_logger().info(f"Socket Ready! Target: {self.rpi_address}")    
        # message to terminal my meesage.

    def listener_callback(self, color_msg, depth_msg):
        try:
            # color_msg & depth_msg are converted into ROS2
            color_image = self.bridge.imgmsg_to_cv2(color_msg, "bgr8") 
            depth_image = self.bridge.imgmsg_to_cv2(depth_msg, "16UC1")
            # data Preprocessing. We use color_image for preprocessing.
            gray = cv2.cvtColor(color_image, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)    
            
            face_detected = False   

            # setting for real target
            closest_dist = float('inf')
            real_offset_x = None
            real_offset_y = None
            target_rect = None

            for (x, y, w, h) in faces:
                face_detected = True
                center_x = x+w//2
                center_y = y+h//2
                
                # offset between face and center of coloar_image.
                offset_x = center_x - depth_image.shape[1]//2
                offset_y = center_y - depth_image.shape[0]//2

                
                if 0<=center_x<color_image.shape[1] and 0<=center_y<color_image.shape[0]:
                    dist_m = depth_image[center_y, center_x] / 1000
                    # all faces are filled with rectangle (green)
                    cv2.rectangle(color_image, (x, y+h), (x+w, y),(0,255,0),1)

                    # closest face are catched 
                    if 0 < dist_m < closest_dist:
                        closest_dist = dist_m
                        real_offset_x = offset_x
                        real_offset_y = offset_y
                        target_rect = (x,y,w,h)
                    

            # real face is not None !!! 
            if real_offset_y is not None and real_offset_x is not None:
                # at that moment we push out data to rasp
                msg = f"{real_offset_x},{real_offset_y}"
                self.sock.sendto(msg.encode(), self.rpi_address)    

                # when target rect is not none, we print the color
                if target_rect:
                    tx, ty, tw, th = target_rect
                    # red rectangle
                    cv2.rectangle(color_image, (tx, ty+th), (tx+tw, ty),(0,0,255),3)
                    cv2.putText(color_image, f"{dist_m:.2f}m", (tx, ty-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)               
            
            if not face_detected:
                pass
            
            # show above information that I make
            cv2.imshow("motor_tracker", color_image)
            cv2.waitKey(1) 

        except Exception as e:
            self.get_logger().error(f'Processing Error: {e}')
            
                    
def main():
    rclpy.init() # for using rclpy functions. Before starting,
    node = MotorTrackerNode() 
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