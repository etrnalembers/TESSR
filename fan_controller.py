
# fan_controller.py
# This script simulates a PWM fan controller.

import time
import os

# --- State File ---
# The main application will write the desired fan speed to this file.
# This simulates an I/O or hardware register interaction.
STATE_FILE = "/tmp/fan_speed.state"

# --- Fan Simulation Parameters ---
DEFAULT_SPEED = 0 # Fan is off by default

def get_desired_speed():
    """Reads the desired fan speed from the state file."""
    if not os.path.exists(STATE_FILE):
        return DEFAULT_SPEED
    try:
        with open(STATE_FILE, 'r') as f:
            speed = int(f.read().strip())
            # Ensure speed is within a valid PWM range (0-100%)
            return max(0, min(100, speed))
    except (ValueError, IOError):
        return DEFAULT_SPEED

if __name__ == "__main__":
    print("--- Starting PWM Fan Controller Simulator ---")
    current_speed = -1 # Initialize to a value that forces the first print
    while True:
        desired_speed = get_desired_speed()
        if current_speed != desired_speed:
            current_speed = desired_speed
            if current_speed == 0:
                print("FAN CONTROLLER: Fan is OFF.")
            else:
                print(f"FAN CONTROLLER: Fan speed set to {current_speed}%.")
        time.sleep(1)
