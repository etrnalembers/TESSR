
import os
import psutil
import shutil
import random
import subprocess
from flask import Flask, send_file, jsonify, request, abort
from werkzeug.utils import secure_filename
from celery.result import AsyncResult

# Import the NPU manager and the Celery task
import npu_manager as npu
from tasks import celery, run_npu_inference_task

# --- Configuration ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(npu.STORAGE_PATH, 'uploads')

# --- Global State Management ---
# Centralized dictionary to hold the state of various simulated components
system_state = {
    "temperature_c": 55.0,
    "fan_speed_percent": 0,
    "diode_state": "off",
    "power_supply_state": "on"
}

# State file paths for controllers
FAN_STATE_FILE = "/tmp/fan_speed.state"
DIODE_STATE_FILE = "/tmp/diode_state.state"


# --- Helper Functions ---
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
    # Return a combined state
    return jsonify({
        "drives": [seagate_health], 
        "raid_arrays": [],
        "system_state": system_state
    })

@app.route('/api/system/temperature', methods=['POST'])
def system_temperature():
    """Endpoint for the temperature simulator to post data to."""
    temp = request.json.get('temperature_c')
    if temp is None:
        return jsonify({"error": "temperature_c not provided"}), 400
    
    system_state['temperature_c'] = temp
    print(f"MAIN APP: Received temperature update: {temp}°C")

    # Reactive logic: if temp is critical, force the fan to 100%
    if temp > 80.0 and system_state['fan_speed_percent'] < 100:
        print("MAIN APP: CRITICAL TEMP DETECTED! Forcing fan to 100%.")
        set_fan_speed(100)
        
    return jsonify({"status": "temperature_received"}), 200

@app.route('/api/system/fan', methods=['GET', 'POST'])
def system_fan():
    """Controls the PWM fan simulator."""
    if request.method == 'POST':
        speed = request.json.get('speed')
        if speed is None or not isinstance(speed, int) or not 0 <= speed <= 100:
            return jsonify({"error": "Invalid speed. Must be an integer between 0 and 100."}), 400
        
        set_fan_speed(speed)
        return jsonify({"message": f"Fan speed set to {speed}%"}), 200
    
    return jsonify({"fan_speed_percent": system_state['fan_speed_percent']})

def set_fan_speed(speed):
    """Helper to update fan speed state and write to the state file."""
    system_state['fan_speed_percent'] = speed
    with open(FAN_STATE_FILE, 'w') as f:
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
    """Controls the mock power supply for the drive array."""
    if request.method == 'POST':
        state = request.json.get('state')
        if state in ['on', 'off']:
            system_state['power_supply_state'] = state
            print(f"MOCK: Optocoupler triggered to turn power supply {state}")
            return jsonify({"message": f"Power supply turning {state}"}), 200
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
    for state_file in [FAN_STATE_FILE, DIODE_STATE_FILE]:
        if os.path.exists(state_file):
            os.remove(state_file)

    print("--- Starting All Simulators ---")
    simulators = [
        "overcurrent_simulator.py",
        "temperature_simulator.py",
        "fan_controller.py",
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
