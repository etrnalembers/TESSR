
import requests
import time
import random

# URL of the Flask app's alert endpoint
ALERT_URL = "http://localhost:5000/api/system/alert"

def simulate_overcurrent_detection():
    """
    Simulates a microcontroller detecting an overcurrent and reporting it.
    """
    print("Simulating overcurrent detection event...")
    
    # Simulate a random chance of an overcurrent event
    if random.random() < 0.1: # 10% chance of overcurrent
        payload = {
            "source": "micropython_controller",
            "event_type": "overcurrent_detected",
            "details": {
                "component": "storage_array_power_bus",
                "current_amps": random.uniform(10.5, 15.0), # Simulate high current
                "threshold_amps": 10.0
            }
        }
        
        try:
            response = requests.post(ALERT_URL, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes
            print(f"Successfully sent overcurrent alert: {payload}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send overcurrent alert: {e}")
    else:
        print("No overcurrent detected in this cycle.")

if __name__ == "__main__":
    print("Starting overcurrent event simulator...")
    while True:
        simulate_overcurrent_detection()
        time.sleep(5) # Wait for 5 seconds before the next check
