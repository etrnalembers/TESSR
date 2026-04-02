
import os
import psutil
import shutil
import random
import subprocess
import requests  # Import the requests library
from flask import Flask, send_file, jsonify, request, abort
from werkzeug.utils import secure_filename
from celery.result import AsyncResult

# Import the NPU manager and the Celery task
import npu_manager as npu
import psu_controller
from tasks import celery, run_npu_inference_task

# --- Configuration ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(npu.STORAGE_PATH, 'uploads')

# --- Global State Management ---
# Centralized dictionary to hold the state of various simulated components
system_state = {
    "temperature_c": 55.0,
    "fan_speeds": {"case_fan": 0, "psu_fan": 0}, # Changed to a dictionary
    "diode_state": "off",
    "power_supply_state": "on"
}

# State file paths for controllers
DIODE_STATE_FILE = "/tmp/diode_state.state"


# --- Helper Functions ---
def get_fan_state_file(fan_id):
    """Returns the state file path for a given fan ID."""
    return f"/tmp/fan_speed_{secure_filename(fan_id)}.state"

def is_safe_path(path):
    """Security check to prevent directory traversal attacks."""
    requested_path = os.path.abspath(os.path.join(npu.STORAGE_PATH, path.lstrip('/')))
    return requested_path.startswith(npu.STORAGE_PATH)

# --- HTML Frontend ---
@app.route("/")
def index():
    return send_file('src/index.html')

# --- System & Simulator API ---
@app.route("/api/system/disks")
def get_disks():
    partitions = psutil.disk_partitions()
    disks = []
    for p in partitions:
        try:
            usage = psutil.disk_usage(p.mountpoint)
            disks.append({
                "device": p.device, "mountpoint": p.mountpoint, "fstype": p.fstype,
                "total": f"{usage.total / (1024**3):.2f} GB",
                "used": f"{usage.used / (1024**3):.2f} GB",
                "free": f"{usage.free / (1024**3):.2f} GB",
                "percent": usage.percent
            })
        except (PermissionError, FileNotFoundError):
            continue
    return jsonify(disks)

@app.route("/api/system/health")
def get_system_health():
    """Returns a mock list of drives and combines with current system state."""
    seagate_health = {
        "manufacturer": "Seagate", "total_gb": 500, "temperature_c": 35,
        "smart_attributes": {"Reallocated_Sector_Ct": 0, "Power_On_Hours": 1200},
        "errors": []
    }
    health_data = {
        "drives": [seagate_health], 
        "raid_arrays": [],
        "system_state": system_state
    }

    # Trigger NPU inference
    try:
        inference_payload = {
            "model_name": "gemma-2b-int4.rknn",
            "input_data": health_data
        }
        # Use the internal request context to call the inference endpoint
        with app.test_request_context():
            response = requests.post(f"http://127.0.0.1:{os.environ.get('PORT', 3177)}/api/npu/inference", json=inference_payload)
            response.raise_for_status() # Raise an exception for bad status codes
            task_id = response.json().get("task_id")
            print(f"MAIN APP: Dispatched NPU inference task {task_id}")
            health_data["inference_task_id"] = task_id
    except requests.exceptions.RequestException as e:
        print(f"MAIN APP: Failed to dispatch NPU task: {e}")
        health_data["inference_error"] = str(e)

    return jsonify(health_data)


@app.route('/api/system/temperature', methods=['POST'])
def system_temperature():
    """Endpoint for the temperature simulator to post data to."""
    temp = request.json.get('temperature_c')
    if temp is None:
        return jsonify({"error": "temperature_c not provided"}), 400
    
    system_state['temperature_c'] = temp
    print(f"MAIN APP: Received temperature update: {temp}°C")

    # Reactive logic: if temp is critical, force the main case fan to 100%
    if temp > 80.0 and system_state['fan_speeds'].get('case_fan', 0) < 100:
        print("MAIN APP: CRITICAL TEMP DETECTED! Forcing case_fan to 100%.")
        set_fan_speed('case_fan', 100)
            
    return jsonify({"status": "temperature_received"}), 200

@app.route('/api/system/fan', methods=['GET', 'POST'])
def system_fan():
    """Controls the PWM fan simulators."""
    if request.method == 'POST':
        data = request.get_json()
        fan_id = data.get('id')
        speed = data.get('speed')

        if not fan_id or speed is None:
            return jsonify({"error": "Request must include 'id' and 'speed'."}), 400
        if fan_id not in system_state['fan_speeds']:
            return jsonify({"error": f"Fan with id '{fan_id}' not found."}), 404
        if not isinstance(speed, int) or not 0 <= speed <= 100:
            return jsonify({"error": "Invalid speed. Must be an integer between 0 and 100."}), 400
        
        set_fan_speed(fan_id, speed)
        return jsonify({"message": f"Fan '{fan_id}' speed set to {speed}%"}), 200
    
    return jsonify({"fan_speeds": system_state['fan_speeds']})

def set_fan_speed(fan_id, speed):
    """Helper to update fan speed state and write to the state file."""
    system_state['fan_speeds'][fan_id] = speed
    state_file = get_fan_state_file(fan_id)
    with open(state_file, 'w') as f:
        f.write(str(speed))

@app.route('/api/system/diode', methods=['GET', 'POST'])
def system_diode():
    """Controls the fault injection diode simulator."""
    if request.method == 'POST':
        state = request.json.get('state')
        if state not in ['on', 'off']:
            return jsonify({"error": "Invalid state. Must be 'on' or 'off'."}), 400
        
        system_state['diode_state'] = state
        with open(DIODE_STATE_FILE, 'w') as f:
            f.write(state)
        return jsonify({"message": f"Fault diode set to {state}"}), 200
        
    return jsonify({"diode_state": system_state['diode_state']})


@app.route('/api/power/array', methods=['GET', 'POST'])
def power_array():
    """Controls the power supply for the drive array (Real and Mock)."""
    if request.method == 'POST':
        state = request.json.get('state')
        
        # Valid states: physically turning it on/off, or mocking emergency surge/loss
        if state in ['on', 'off', 'power_surge', 'power_loss']:
            system_state['power_supply_state'] = state
            
            if npu.IS_REAL_MODE:
                # We are running with physical hardware access
                if state == 'on':
                    psu_controller.turn_on_psu()
                    print("REAL: Optocoupler triggered to turn power supply ON (HIGH)")
                elif state == 'off':
                    psu_controller.turn_off_psu()
                    print("REAL: Optocoupler triggered to turn power supply OFF (LOW)")
                elif state in ['power_surge', 'power_loss']:
                    psu_controller.trigger_emergency_fallback()
                    print(f"REAL: Emergency Fallback triggered due to {state}. Active LOW shutdown initiated.")
            else:
                # We are in the sandbox/mock environment
                print(f"MOCK: Optocoupler mock-triggered. State changed to: {state}")
                if state in ['power_surge', 'power_loss']:
                    print(f"MOCK: Simulating emergency fault scenario: {state}")
            
            return jsonify({"message": f"Power supply set to {state}"}), 200
        
        return jsonify({"error": "Invalid state"}), 400
    
    return jsonify({"power_supply_state": system_state['power_supply_state']})

# --- NPU API (Asynchronous) ---
@app.route("/api/npu/status")
def npu_status_route():
    return jsonify(npu.get_npu_status())

@app.route("/api/npu/models")
def npu_models_route():
    return jsonify(npu.get_available_models())

@app.route("/api/npu/inference", methods=['POST'])
def npu_inference_route():
    model_name = request.json.get("model_name")
    input_data = request.json.get("input_data")
    if not model_name or not input_data:
        return jsonify({"error": "model_name and input_data are required"}), 400
    task = run_npu_inference_task.delay(model_name, input_data)
    return jsonify({"task_id": task.id, "status": "pending"}), 202

@app.route("/api/npu/result/<string:task_id>", methods=['GET'])
def get_npu_result_route(task_id):
    task_result = AsyncResult(task_id, app=celery)
    if task_result.ready():
        if task_result.successful():
            return jsonify({
                "task_id": task_id,
                "status": "completed",
                "result": task_result.result
            })
        else:
            return jsonify({
                "task_id": task_id,
                "status": "failed",
                "error": str(task_result.info)
            }), 500
    else:
        return jsonify({"task_id": task_id, "status": "pending"}), 202

# --- File Management API (Omitted for brevity, assumed unchanged) ---
# ...

# --- Main Application Runner ---
def main():
    # Clean up old state files on start
    for fan_id in system_state['fan_speeds']:
        state_file = get_fan_state_file(fan_id)
        if os.path.exists(state_file):
            os.remove(state_file)
    if os.path.exists(DIODE_STATE_FILE):
        os.remove(DIODE_STATE_FILE)

    if npu.IS_REAL_MODE:
        print("--- Initializing Hardware Controllers ---")
        psu_controller.initialize()

    print("--- Starting All Simulators ---")
    # Start fan controllers
    for fan_id in system_state['fan_speeds']:
        try:
            subprocess.Popen([".venv/bin/python", "fan_controller.py", "--fan-id", fan_id])
            print(f"Launched fan_controller.py for '{fan_id}'.")
        except FileNotFoundError:
            print(f"ERROR: Could not find fan_controller.py.")

    # Start other simulators
    simulators = [
        "overcurrent_simulator.py",
        "temperature_simulator.py",
        "diode_controller.py"
    ]
    for sim in simulators:
        try:
            subprocess.Popen([".venv/bin/python", sim])
            print(f"Launched {sim}.")
        except FileNotFoundError:
            print(f"ERROR: Could not find {sim}. Make sure it exists.")


    print("\nReminder: Start Redis and the Celery worker in separate terminals.")
    print("  docker run -d -p 6379:6379 redis")
    print("  celery -A tasks.celery worker --loglevel=info\n")
    
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 3177)))

if __name__ == "__main__":
    main()
