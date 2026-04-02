# npu_real.py
# This file contains the REAL implementation for the Rockchip NPU.

import os
import logging

try:
    from rknnlite.api import RKNNLite # Use this when on actual hardware
except ImportError:
    RKNNLite = None
    logging.warning("Safe-Boot Warning: rknnlite not found. NPU Sensors bypassed for initial PSU stress-test run.")

# --- Constants ---
# This path will point to the INT4 quantized Gemma 2B model.
# The conversion to this format is done offline using the RKNN-Toolkit2.
QUANTIZED_MODEL_PATH = "models/gemma-2b-int4.rknn"

# --- Global State ---
# This will hold the loaded RKNNLite model instance.
# We load the model only once to save memory and startup time.
_rknn_lite = None

def get_npu_status():
    """Returns the detailed status of the NPU."""
    global _rknn_lite
    
    # SAFE-BOOT: We bypass full sensor checks while testing the PSU optocoupler
    if RKNNLite is None:
        return {"npu_status": "bypassed_safe_mode", "loaded_model": None, "message": "NPU bypassed for PSU stress test."}
        
    if _rknn_lite is None:
        # In a real scenario, you might query the driver for temperature, clock speed, etc.
        return {"npu_status": "available", "loaded_model": None}
    
    # Once loaded, you could add more details.
    return {
        "npu_status": "active",
        "loaded_model": os.path.basename(QUANTIZED_MODEL_PATH),
        "memory_usage_mb": 1900, # Placeholder for INT4
        "performance_tops": 0.7 # Based on hardware specs
    }

def load_model(model_name=None):
    """
    Loads the quantized model into memory using RKNNLite.
    """
    global _rknn_lite
    if _rknn_lite is not None:
        print("INFO: Model is already loaded.")
        return True, "Model already loaded."

    if not os.path.exists(QUANTIZED_MODEL_PATH):
        msg = f"ERROR: Model file not found at {QUANTIZED_MODEL_PATH}. Run conversion scripts first."
        print(msg)
        return False, msg

    print(f"INFO: Loading quantized model from {QUANTIZED_MODEL_PATH}...")
    try:
        _rknn_lite = RKNNLite()
        ret = _rknn_lite.load_rknn(QUANTIZED_MODEL_PATH)
        if ret != 0:
            print("ERROR: Failed to load RKNN model.")
            _rknn_lite = None
            return False, "Failed to load RKNN model file."
        print("INFO: Model loaded successfully.")
        # This is where you would initialize the NPU context if needed.
        _rknn_lite.init_runtime()
    except Exception as e:
        print(f"ERROR: An exception occurred while loading the model: {e}")
        _rknn_lite = None
        return False, str(e)

    return True, "Model loaded successfully."

def unload_model(model_name=None):
    """Releases the model from memory."""
    global _rknn_lite
    if _rknn_lite is not None:
        _rknn_lite.release()
        _rknn_lite = None
        print("INFO: Model unloaded.")
    return True, "Model unloaded."

def run_inference(model_name, input_data):
    """
    Runs inference on the loaded RKNN model.
    This function is now a placeholder and will be called by a Celery task.
    """
    global _rknn_lite
    if _rknn_lite is None:
        msg = "ERROR: Model is not loaded. Cannot run inference."
        print(msg)
        return None, msg
    
    print(f"INFO: Running inference on NPU with input: {input_data}")
    
    # 1. Pre-process the input_data into the format the model expects.
    #    (e.g., tokenization for a language model).
    
    # 2. Run the inference.
    outputs = _rknn_lite.inference(inputs=[input_data])
    
    # 3. Post-process the output to a human-readable format.
    
    return outputs, "Inference completed successfully."

def get_available_models():
    """Returns a list of models available for the real NPU."""
    if os.path.exists(QUANTIZED_MODEL_PATH):
        return [os.path.basename(QUANTIZED_MODEL_PATH)]
    return []
