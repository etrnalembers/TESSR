# tasks.py
# This file defines the Celery tasks for background processing.

import os
from celery import Celery

# Import the NPU manager, which will point to the correct implementation (real or mock)
import npu_manager as npu

# --- Celery Configuration ---
# The broker URL points to Redis, which acts as the message queue.
# The backend URL also points to Redis, where results will be stored.
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize Celery
celery = Celery(__name__, broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# --- Asynchronous NPU Task ---
@celery.task(name='tasks.run_npu_inference')
def run_npu_inference_task(model_name, input_data):
    """
    A Celery task that wraps the run_inference function from the NPU manager.
    
    This runs in a separate Celery worker process, so it doesn't block the main
    Flask application. The NPU model is loaded once per worker.
    """
    # Ensure the model is loaded in the worker process.
    # Celery workers are long-lived, so this will only run on worker startup.
    loaded, msg = npu.load_model(model_name)
    if not loaded:
        # If the model fails to load, we can't proceed.
        return {"error": f"Model ({model_name}) could not be loaded in worker: {msg}"}
    
    print(f"CELERY WORKER: Starting inference for model '{model_name}'.")
    
    # Run the actual inference using the function provided by the NPU manager.
    # This will call either the real or mock implementation.
    results, message = npu.run_inference(model_name, input_data)
    
    if results is None:
        return {"error": message}
        
    return {"results": results, "message": message}
