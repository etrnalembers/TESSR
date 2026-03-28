# npu_mock.py
# This file contains the mock implementation for the NPU.
# It allows the application to run on any machine for development and testing.

import random
import json

# --- Mock Data and State ---
MOCK_MODEL_PATH = "models/gemma-2b-int4.rknn"
_mock_model_loaded = False

def get_npu_status():
    """Mock status for non-Orange Pi systems."""
    global _mock_model_loaded
    if not _mock_model_loaded:
        return {"npu_status": "available", "loaded_model": None}
    
    return {
        "npu_status": "active",
        "loaded_model": "gemma-2b-int4.rknn",
        "memory_usage_mb": 1900,
        "performance_tops": 0.0 # Mock performance
    }

def get_available_models():
    """Returns a list of mock models."""
    return ["gemma-2b-int4.rknn"]

def load_model(model_name=None):
    """Mocks loading the model."""
    global _mock_model_loaded
    if _mock_model_loaded:
        return True, "Model is already loaded"
    
    print(f"MOCK: Loading model {model_name}")
    _mock_model_loaded = True
    return True, f"{model_name} loaded successfully (mock)"

def unload_model(model_name=None):
    """Mocks unloading the model."""
    global _mock_model_loaded
    if not _mock_model_loaded:
        return True, "Model is not loaded or already unloaded"

    print(f"MOCK: Unloading model {model_name}")
    _mock_model_loaded = False
    return True, f"{model_name} unloaded successfully (mock)"

def run_inference(model_name, input_data):
    """
    Mocks running inference on the loaded model.
    It returns a predefined response based on keywords in the input data.
    """
    global _mock_model_loaded
    if not _mock_model_loaded:
        return None, "Model is not loaded"

    print(f"MOCK: Running inference with {model_name} on input: {input_data}")

    # Simple logic to simulate different responses based on input
    input_str = json.dumps(input_data)
    if "High Temperature Alert" in input_str:
        mock_result = {
            "thought": "A drive is overheating. I will power off the array to let it cool down.",
            "action": {
                "tool": "/api/power/array",
                "method": "POST",
                "params": {"state": "off"}
            }
        }
    elif "degraded" in input_str:
        mock_result = {
            "thought": "The RAID array is in a degraded state. I will notify the user.",
            "action": {
                "tool": "/api/notifications/send",
                "method": "POST",
                "params": {"level": "critical", "message": "RAID array is DEGRADED. Data is at risk. Replace failed drive immediately."}
            }
        }
    else:
        mock_result = {
            "thought": "System health is nominal. No action required.",
            "action": {}
        }
        
    return mock_result, "Inference complete (mock)"
