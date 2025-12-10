# npu_mock.py
# This file contains the mock implementation for the NPU.
# It allows the application to run on any machine for development and testing.

import random

# --- Mock Data and State ---
MOCK_MODEL_PATH = "models/yolov5s.rknn"
mock_models = {
    "yolov5s": {"path": MOCK_MODEL_PATH, "state": "unloaded"},
    "resnet18": {"path": "models/resnet18.rknn", "state": "unloaded"}
}

def get_npu_status():
    """Mock status for non-Orange Pi systems."""
    return {
        "npu_type": "Mock NPU",
        "driver_version": "N/A",
        "npu_load_percent": 0,
        "available_memory_mb": 0,
        "cpu_temperature_c": 0,
        "npu_status": "unavailable",
        "errors": ["Running on a non-Orange Pi device. NPU is mocked."]
    }

def get_available_models():
    return list(mock_models.keys())

def load_model(model_name):
    if model_name not in mock_models:
        return False, "Model not found"
    if mock_models[model_name]["state"] == "loaded":
        return True, "Model is already loaded"
    
    print(f"MOCK: Loading model {model_name}")
    mock_models[model_name]["state"] = "loaded"
    return True, f"{model_name} loaded successfully (mock)"

def unload_model(model_name):
    if model_name not in mock_models or mock_models[model_name]["state"] == "unloaded":
        return True, "Model is not loaded or already unloaded"

    print(f"MOCK: Unloading model {model_name}")
    mock_models[model_name]["state"] = "unloaded"
    return True, f"{model_name} unloaded successfully (mock)"

def run_inference(model_name, input_data):
    if model_name not in mock_models or mock_models[model_name]["state"] != "loaded":
        return None, "Model is not loaded"

    print(f"MOCK: Running inference with {model_name}")
    # Return a generic, predictable mock result
    return {"results": [{"label": "cat", "confidence": 0.92, "box": [100, 150, 300, 400]}]}, "Inference complete (mock)"
