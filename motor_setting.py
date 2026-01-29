from time import sleep
import RPi.GPIO as GPIO

# pin number of Rasp
TILT_PIN = 18
# normal duty range
SERVO_MAX_DUTY = 12
SERVO_MIN_DUTY = 3

# GPIO setting. We set GPIO as BCM. It means PIN number 17 = board number 11 
GPIO.setmode(GPIO.BCM) 
# GPIO output = PAN_PIN (17)
GPIO.setup(TILT_PIN, GPIO.OUT)

# MG996r => use 50Hz
TILTservo = GPIO.PWM(TILT_PIN, 50)
TILTservo.start(0)

print("Motor control ready!")

def TILTsetServoPos(TILTdegree):
    if TILTdegree > 180:
        TILTdegree = 180
    if TILTdegree <0:
        TILTdegree = 0

    TILTduty = SERVO_MIN_DUTY + (TILTdegree*(SERVO_MAX_DUTY-SERVO_MIN_DUTY)/180)
    print("TILTDegree: {} to {}(duty)".format(TILTdegree, TILTduty))
    TILTservo.ChangeDutyCycle(TILTduty)

if __name__ == "__main__":
    try:
        TILTdegree = 90
        TILTsetServoPos(TILTdegree) 
        sleep(1)

    except KeyboardInterrupt:
        print("\nExit.")
        
    finally: 
        TILTservo.stop()
        del TILTservo 
        GPIO.cleanup()