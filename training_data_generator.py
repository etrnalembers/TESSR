# training_data_generator.py

import json
import random

# This script generates training data for fine-tuning an SLM to manage the storage array.
# It defines a series of scenarios and the ideal sequence of API calls (the "plan") 
# that the SLM should make in response.

# --- Helper functions to simulate API calls ---
# In a real scenario, these would make HTTP requests to the running Flask app.
# For data generation, we can use the logic directly from main.py's mock endpoints.

def get_mock_system_health():
    """Simulates a call to /api/system/health, returning one of several failure states."""
    seagate_health = {"manufacturer": "Seagate", "total_gb": 500, "temperature_c": 35, "smart_attributes": {"Reallocated_Sector_Ct": 0}, "errors": []}
    wd_drives_health = [{"manufacturer": "Western Digital", "total_gb": 1000, "temperature_c": 40, "smart_attributes": {"Reallocated_Sector_Ct": 0}, "errors": []} for _ in range(4)]
    raid_status = {"array": "/dev/md0", "level": 5, "status": "active", "sync_percent": 100, "errors": []}

    scenario = random.choice(["healthy", "temp_warning", "lifespan_warning", "sync_error", "corruption"])

    if scenario == "temp_warning":
        seagate_health["temperature_c"] = 68
        seagate_health["errors"].append("High Temperature Alert")
    elif scenario == "lifespan_warning":
        wd_drives_health[2]["smart_attributes"]["Reallocated_Sector_Ct"] = 175
        wd_drives_health[2]["errors"].append("S.M.A.R.T. Lifespan Warning")
    elif scenario == "sync_error":
        raid_status["status"] = "degraded"
        raid_status["errors"] = ["Disk 2 failed. Array is in degraded mode."]
    elif scenario == "corruption":
        wd_drives_health[0]["errors"].append("Uncorrectable I/O Error: Filesystem may be corrupt.")

    return {"drives": [seagate_health] + wd_drives_health, "raid_arrays": [raid_status]}

def get_mock_pi_status():
    """Simulates a call to /api/npu/status with Pi-specific failures."""
    status = {"mode": "mock", "drivers_found": False}
    scenario = random.choice(["healthy", "overheating", "npu_lockup"])
    if scenario == "overheating":
        status['cpu_temperature_c'] = 88
        status['errors'] = ["CPU temperature critical"]
    elif scenario == "npu_lockup":
        status['npu_status'] = "error"
        status['errors'] = ["NPU core unresponsive"]
    else:
        status['cpu_temperature_c'] = 55
        status['errors'] = []
    return status

# --- Training Data Generation Logic ---

def generate_training_example():
    """Creates a single training example (input prompt + ideal output)."""
    
    # 1. Simulate the state of the world by calling the mock APIs
    pi_state = get_mock_pi_status()
    drive_state = get_mock_system_health()

    # 2. Construct the input prompt for the SLM
    # This is what the SLM "sees". It's a summary of the system status.
    prompt = f"USER: Assess system status and take necessary action.\nASSISTANT (thought): I need to check the status of the Orange Pi and the storage array. First, I will call the system health and NPU status APIs.\nASSISTANT (API call): GET /api/system/health -> {json.dumps(drive_state)}\nASSISTANT (API call): GET /api/npu/status -> {json.dumps(pi_state)}\nASSISTANT (thought): Now I will analyze the data and form a plan."
    
    # 3. Determine the correct plan of action based on the state (The "brains" of the generator)
    plan = []
    
    # -- Rule-based logic to define the correct response for each scenario --

    # Priority 1: Orange Pi is overheating
    if "CPU temperature critical" in pi_state.get('errors', []):
        plan.append({"thought": "The Orange Pi CPU is critically overheating. The highest priority is to shut down attached high-power peripherals to reduce load and prevent damage. I will turn off the drive array power supply.",
                     "action": {"tool": "/api/power/array", "method": "POST", "params": {"state": "off"}}})
        plan.append({"thought": "Now I must alert the user about the critical CPU temperature.",
                     "action": {"tool": "/api/notifications/send", "method": "POST", "params": {"level": "critical", "message": "Orange Pi CPU is overheating. Shutting down drive array to prevent damage."}}})
    
    # Priority 2: A drive is about to fail (lifespan)
    elif any("S.M.A.R.T. Lifespan Warning" in d.get('errors', []) for d in drive_state['drives']):
        plan.append({"thought": "A drive is reporting a S.M.A.R.T. lifespan warning, indicating imminent failure. I should safely power down the array to allow for physical replacement.",
                     "action": {"tool": "/api/power/array", "method": "POST", "params": {"state": "off"}}})
        plan.append({"thought": "I need to inform the user about the specific failing drive.",
                     "action": {"tool": "/api/notifications/send", "method": 'POST', "params": {"level": "error", "message": "Drive failure predicted by S.M.A.R.T. data. Powering down array for maintenance."}}})

    # Priority 3: A drive is overheating
    elif any("High Temperature Alert" in d.get('errors', []) for d in drive_state['drives']):
        plan.append({"thought": "A drive is overheating. I will power off the array to let it cool down.",
                     "action": {"tool": "/api/power/array", "method": "POST", "params": {"state": "off"}}})
        plan.append({"thought": "I should notify the user of the temperature issue.",
                     "action": {"tool": "/api/notifications/send", "method": "POST", "params": {"level": "warning", "message": "A drive is overheating. Array has been powered down."}}})

    # Priority 4: RAID array is degraded
    elif any("degraded" in r.get('status', "") for r in drive_state['raid_arrays']):
        plan.append({"thought": "The RAID array is in a degraded state. File access is still possible but there is no redundancy. I will not power it down, but I must alert the user immediately.",
                     "action": {"tool": "/api/notifications/send", "method": "POST", "params": {"level": "critical", "message": "RAID array is DEGRADED. Data is at risk. Replace failed drive immediately."}}})

    # Default case: Everything is healthy
    else:
        plan.append({"thought": "System health is nominal. No action required.", "action": {}})

    # 4. Format the final training example
    return {
        "prompt": prompt,
        "completion": json.dumps(plan)
    }

# --- Main Execution ---
if __name__ == "__main__":
    dataset = [generate_training_example() for _ in range(200)] # Generate 200 examples
    
    # Save to a file in a format suitable for fine-tuning (e.g., JSON Lines)
    with open("storage_management_training_data.jsonl", "w") as f:
        for entry in dataset:
            f.write(json.dumps(entry) + "\n")
            
    print(f"Successfully generated {len(dataset)} training examples.")
    print("Dataset saved to 'storage_management_training_data.jsonl'")
