# fan_controller.py
# This script simulates a PWM fan controller for a specific fan.

import time
import os
import argparse
from werkzeug.utils import secure_filename

# --- Fan Simulation Parameters ---
DEFAULT_SPEED = 0 # Fan is off by default

def get_state_file_path(fan_id):
    """Constructs the state file path based on the fan ID."""
    return f"/tmp/fan_speed_{secure_filename(fan_id)}.state"

def get_desired_speed(state_file):
    """Reads the desired fan speed from the given state file."""
    if not os.path.exists(state_file):
        return DEFAULT_SPEED
    try:
        with open(state_file, 'r') as f:
            speed = int(f.read().strip())
            # Ensure speed is within a valid PWM range (0-100%)
            return max(0, min(100, speed))
    except (ValueError, IOError):
        return DEFAULT_SPEED

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PWM Fan Controller Simulator")
    parser.add_argument("--fan-id", type=str, required=True, help="The unique identifier for the fan to control.")
    args = parser.parse_args()

    fan_id = args.fan_id
    state_file = get_state_file_path(fan_id)
    
    print(f"--- Starting PWM Fan Controller for '{fan_id}' ---")
    print(f"Monitoring state file: {state_file}")

    current_speed = -1 # Initialize to a value that forces the first print
    while True:
        desired_speed = get_desired_speed(state_file)
        if current_speed != desired_speed:
            current_speed = desired_speed
            if current_speed == 0:
                print(f"FAN CONTROLLER ({fan_id}): Fan is OFF.")
            else:
                print(f"FAN CONTROLLER ({fan_id}): Fan speed set to {current_speed}%.")
        time.sleep(1)
