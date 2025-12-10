
# diode_controller.py
# This script simulates a controller for a fault-injection diode.

import time
import os

# --- State File ---
# The main application will write the desired state to this file.
STATE_FILE = "/tmp/diode_state.state"

def get_diode_state():
    """Reads the desired diode state ('on' or 'off') from the state file."""
    if not os.path.exists(STATE_FILE):
        return "off"
    try:
        with open(STATE_FILE, 'r') as f:
            state = f.read().strip().lower()
            return state if state in ["on", "off"] else "off"
    except (ValueError, IOError):
        return "off"

if __name__ == "__main__":
    print("--- Starting Fault Diode Controller Simulator ---")
    current_state = ""
    while True:
        desired_state = get_diode_state()
        if current_state != desired_state:
            current_state = desired_state
            if current_state == "on":
                print("DIODE CONTROLLER: Diode is ON. (Simulating fault condition)")
            else:
                print("DIODE CONTROLLER: Diode is OFF. (Normal operation)")
        time.sleep(1)
