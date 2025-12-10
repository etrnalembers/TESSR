# npu_manager.py
# This file acts as a dispatcher, providing the correct NPU implementation
# and managing data storage paths for real vs. mock environments.

import os

# --- Configuration for Data Storage ---
REAL_STORAGE_PATH = os.path.abspath("storage_real")
MOCK_STORAGE_PATH = os.path.abspath("storage_mock")

# --- Hardware Detection ---
# This is the single source of truth for hardware detection.
# It checks for a device tree file unique to Orange Pi boards with RK chips.
IS_ORANGE_PI = os.path.exists("/proc/device-tree/compatible") and \
                 "rockchip" in open("/proc/device-tree/compatible").read()

# --- Strategy Pattern Implementation ---
# Based on the hardware detection, we select the appropriate implementation
# and set the active storage path.

if IS_ORANGE_PI:
    print("INFO: Real Orange Pi hardware detected. Loading REAL NPU implementation.")
    IS_REAL_MODE = True
    STORAGE_PATH = REAL_STORAGE_PATH
    
    # The following functions are now sourced directly from npu_real.py
    from npu_real import (
        get_npu_status,
        get_available_models,
        load_model,
        unload_model,
        run_inference
    )
else:
    print("INFO: No Orange Pi hardware detected. Loading MOCK NPU implementation.")
    IS_REAL_MODE = False
    STORAGE_PATH = MOCK_STORAGE_PATH
    
    # The following functions are now sourced directly from npu_mock.py
    from npu_mock import (
        get_npu_status,
        get_available_models,
        load_model,
        unload_model,
        run_inference
    )

# Ensure the selected storage directory exists.
if not os.path.exists(STORAGE_PATH):
    print(f"INFO: Creating storage directory at {STORAGE_PATH}")
    os.makedirs(os.path.join(STORAGE_PATH, 'uploads'))

# By the time another module imports from 'npu_manager', the functions and constants
# above will be correctly pointing to either the real or mock version.