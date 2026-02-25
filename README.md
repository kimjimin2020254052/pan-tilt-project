1.  realsense 카메라 작동
ros2 launch realsense2_camera rs_launch.py align_depth.enable:=true

2. main 파일 작동
ros2 run my_face_tracker practice_tracker

3. ros2 내부 파일 수정시
cd ~/ros2_ws
colcon build --symlink-install
soure install/setup.bash	

4. Raspberrypi 연결시
binoy@ip_address
192.168.0.221
=> password : pi

5. terminator
# 좌우로 분할
Ctrl+Shift+E

# 상하로 분할
Ctrl+Shift+O
