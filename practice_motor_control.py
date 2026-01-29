from time import sleep
import RPi.GPIO as GPIO
import socket

# all data can be received
HOST = '0.0.0.0'
PORT = 5005

# pin number of Rasp
PAN_PIN = 17
TILT_PIN = 18
# normal duty range
SERVO_MAX_DUTY = 12
SERVO_MIN_DUTY = 3
# P-gain
k_p = 0.01

# Deadband => when abs(offset) < 20, it doesn't work  
deadband = 20

# GPIO setting. We set GPIO as BCM. It means PIN number 17 = board number 11 
GPIO.setmode(GPIO.BCM) 
# GPIO output = PAN_PIN (17)
GPIO.setup(PAN_PIN, GPIO.OUT)
GPIO.setup(TILT_PIN, GPIO.OUT)

# MG996r => use 50Hz
PANservo = GPIO.PWM(PAN_PIN, 50)
PANservo.start(0)
TILTservo = GPIO.PWM(TILT_PIN, 50)
TILTservo.start(0)

# We can get some data from realsense
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print("Motor control ready!")

# for moving PAN direction 
def PANsetServoPos(PANdegree):
    if PANdegree > 180:
        PANdegree = 180
    if PANdegree <0:
        PANdegree = 0

    PANduty = SERVO_MIN_DUTY + (PANdegree*(SERVO_MAX_DUTY-SERVO_MIN_DUTY)/180)
    print("PANDegree: {} to {}(duty)".format(PANdegree, PANduty))
    PANservo.ChangeDutyCycle(PANduty)

# for moving TILT direction
def TILTsetServoPos(TILTdegree):
    if TILTdegree > 180:
        TILTdegree = 180
    if TILTdegree <0:
        TILTdegree = 0

    TILTduty = SERVO_MIN_DUTY + (TILTdegree*(SERVO_MAX_DUTY-SERVO_MIN_DUTY)/180)
    print("TILTDegree: {} to {}(duty)".format(TILTdegree, TILTduty))
    TILTservo.ChangeDutyCycle(TILTduty)

if __name__ == "__main__":
    PANdegree = 90
    TILTdegree = 90
    PANsetServoPos(PANdegree)
    TILTsetServoPos(TILTdegree)
    try:
        while True:
            # recvfrom -> waiting the data
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8')
            try:

                parts = message.split(',')
                
                # when part is not None, we can get offset_x 
                if len(parts) > 1:
                    offset_x = float(parts[0])
                else:
                    continue
                if len(parts) > 1:
                    offset_y = float(parts[1])
                else:
                    continue

                # when offset_x > 
                if abs(offset_x) > deadband:
                    PANdegree -= (offset_x*k_p)
                    PANsetServoPos(PANdegree)
                else:
                    # we make Duty of servo is 0. So it will stop when < deadband
                    PANservo.ChangeDutyCycle(0)

                if abs(offset_y) > deadband:
                    TILTdegree -= (offset_y*k_p)
                    TILTsetServoPos(TILTdegree)
                else:
                    TILTservo.ChangeDutyCycle(0)

            except ValueError:
                print(f"Data error: {message}")

    except KeyboardInterrupt:
        print("\nExit.")
        PANservo.stop()
        TILTservo.stop()
        GPIO.cleanup()
        sock.close()