
# temperature_simulator.py
# This script simulates the temperature sensor of the Orange Pi.

import time
import random
import requests
import os

# The endpoint of the main Flask application that will receive the temperature data
HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
PORT = os.environ.get("FLASK_PORT", 3177)
ALERT_URL = f"http://{HOST}:{PORT}/api/system/temperature"

# --- Temperature Simulation Parameters ---
# A healthy baseline temperature
BASE_TEMP = 55.0
# The maximum random fluctuation above the base temperature
TEMP_JITTER = 5.0
# The chance (out of 100) that a critical overheat event will occur
OVERHEAT_CHANCE = 3

def simulate_temperature():
    """
    Simulates CPU temperature, with a small chance of a critical overheat event
    that requires intervention (e.g., triggering the fan).
    """
    current_temp = BASE_TEMP + random.uniform(0, TEMP_JITTER)

    # Occasionally spike the temperature to test the system's reaction
    if random.randint(1, 100) <= OVERHEAT_CHANCE:
        current_temp = 85.0 + random.uniform(0, 5.0)
        print(f"SIMULATOR: CRITICAL - Simulating overheat event: {current_temp:.2f}°C")
    else:
        print(f"SIMULATOR: INFO - Simulating normal temperature: {current_temp:.2f}°C")

    try:
        # Send the simulated temperature to the main application
        response = requests.post(ALERT_URL, json={"temperature_c": current_temp}, timeout=2)
        if response.status_code != 200:
            print(f"SIMULATOR: ERROR - Failed to send temperature data: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"SIMULATOR: ERROR - Could not connect to main application: {e}")


if __name__ == "__main__":
    print("--- Starting Temperature Simulator ---")
    while True:
        simulate_temperature()
        # Wait for a random interval to make the simulation more realistic
        time.sleep(random.randint(5, 15))
