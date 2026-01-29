import socket
import pigpio
from time import sleep

# --- [Configuration] ---
HOST = '0.0.0.0'
PORT = 5005
PAN_PIN = 17 

# Create pigpio object (connect to daemon)
pi = pigpio.pi()

if not pi.connected:
    print("❌ pigpio daemon is not running!")
    print("Please run 'sudo pigpiod' in the terminal first.")
    exit()

# Current angle variables (Only Pan)
curr_pan = 90.0

# [Core Function] Convert angle to Pulse Width to control motor
# Based on MG996R: 0 deg = 500us, 180 deg = 2500us
def move_servo(pin, angle):
    # Safety: Limit between 0 and 180 degrees
    angle = max(0.0, min(180.0, angle))
    
    # Conversion formula: 500 + (angle / 180) * 2000
    pulse_width = 500 + (angle / 180.0) * 2000
    
    # Send pigpio command
    pi.set_servo_pulsewidth(pin, pulse_width)

# Move to initial position (Center)
print("🔧 Initializing Pan Motor to 90 degrees...")
move_servo(PAN_PIN, curr_pan)

# --- [Start Socket Communication] ---
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"📡 Waiting for data... (PORT: {PORT})")
print("✅ Motor control ready! (Pan Only Mode)")

try:
    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode('utf-8')
        
        try:
            # Parse data (Format: "offset_x,offset_y")
            # We split by comma but only use the first value (x)
            parts = message.split(',')
            if len(parts) >= 1:
                offset_x = float(parts[0])
            else:
                continue # Skip if data is invalid
            
            k_p = 0.05
            
            # Calculate angle (Pan Only)
            # If the motor moves in the opposite direction, change '-=' to '+='
            curr_pan -= (offset_x * k_p)
            
            # Limit angle (0~180 degrees)
            curr_pan = max(0.0, min(180.0, curr_pan))
            
            # Move motor
            move_servo(PAN_PIN, curr_pan)
            
            print(f"Received X-Offset: {int(offset_x)} -> Pan Angle: {curr_pan:.1f}")
            
        except ValueError:
            print(f"Data error: {message}")

except KeyboardInterrupt:
    print("\nExiting.")
    # Release motor on exit (0)
    pi.set_servo_pulsewidth(PAN_PIN, 0)
    pi.stop()
    sock.close()
