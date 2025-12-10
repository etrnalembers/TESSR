
import requests
import json
import time

# --- Configuration ---
# This should be the address of your Flask application.
# If running locally, it's likely localhost or 127.0.0.1
BASE_URL = "http://127.0.0.1:8080"

# --- Helper Functions ---
def print_header(title):
    print("\n" + "="*50)
    print(f"--- {title} ---")
    print("="*50)

def print_response(response):
    """Prints the JSON response in a readable format."""
    try:
        print(json.dumps(response.json(), indent=2))
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON. Status: {response.status_code}, Body: {response.text}")

# --- SLM Action Simulations ---

def get_system_status():
    """Simulates the SLM asking for the system's hardware status."""
    print_header("TASK: Get System Status")
    print("SLM: 'What is the current status of the disk and NPU?'")
    
    print("\n--> Checking disks...")
    response_disks = requests.get(f"{BASE_URL}/api/system/disks")
    print_response(response_disks)

    print("\n--> Checking NPU...")
    response_npu = requests.get(f"{BASE_URL}/api/npu/status")
    print_response(response_npu)

def manage_ai_models():
    """Simulates the SLM loading a model, running inference, and unloading it."""
    print_header("TASK: Manage and Use AI Models")
    model_to_use = "image-classification-resnet"

    print(f"SLM: 'Load the {model_to_use} model for me.'")
    response = requests.post(f"{BASE_URL}/api/npu/load", json={"model_name": model_to_use})
    print_response(response)
    time.sleep(1)

    print(f"\nSLM: 'Now, run inference using the {model_to_use} model.'")
    response = requests.post(f"{BASE_URL}/api/npu/inference", json={"model_name": model_to_use})
    print_response(response)
    time.sleep(1)

    print(f"\nSLM: 'Okay, you can unload the {model_to_use} model now.'")
    response = requests.post(f"{BASE_URL}/api/npu/unload", json={"model_name": model_to_use})
    print_response(response)
    time.sleep(1)

    print("\n--> Verifying model states after operations:")
    response = requests.get(f"{BASE_URL}/api/npu/models")
    print_response(response)

def organize_files():
    """Simulates the SLM performing a series of file management tasks."""
    print_header("TASK: Organize Files")
    
    # 1. Create a new directory
    new_folder_path = "/project-alpha"
    print(f"SLM: 'Create a new folder named {new_folder_path}.'")
    response = requests.post(f"{BASE_URL}/api/files/folder", json={"path": new_folder_path})
    print_response(response)
    time.sleep(1)
    
    # 2. Browse the root directory to see the new folder
    print("\nSLM: 'Show me the contents of the root directory.'")
    response = requests.get(f"{BASE_URL}/api/files/browse?path=/")
    print_response(response)
    time.sleep(1)

    # 3. Rename the directory
    new_folder_path_renamed = "/project-pegasus"
    print(f"SLM: 'Rename {new_folder_path} to {new_folder_path_renamed}.'")
    response = requests.put(f"{BASE_URL}/api/files/manage", json={
        "path": new_folder_path,
        "destination": new_folder_path_renamed
    })
    print_response(response)
    time.sleep(1)

    # 4. Browse the root again to see the change
    print("\nSLM: 'Show me the contents of the root directory again.'")
    response = requests.get(f"{BASE_URL}/api/files/browse?path=/")
    print_response(response)
    time.sleep(1)

    # 5. Delete the directory
    print(f"SLM: 'Delete the {new_folder_path_renamed} folder.'")
    response = requests.delete(f"{BASE_URL}/api/files/manage", json={"path": new_folder_path_renamed})
    print_response(response)
    time.sleep(1)
    
    # 6. Final verification
    print("\nSLM: 'Verify the folder is gone.'")
    response = requests.get(f"{BASE_URL}/api/files/browse?path=/")
    print_response(response)

if __name__ == "__main__":
    print("--- SLM SIMULATOR STARTING ---")
    print(f"Targeting API Base URL: {BASE_URL}")
    
    # Run through the simulated scenarios
    get_system_status()
    manage_ai_models()
    organize_files()
    
    print("\n--- SLM SIMULATOR FINISHED ---")
