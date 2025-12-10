# Project Startup and Tool Commands

This document provides all the necessary commands and instructions for setting up, running, and interacting with the Flask-based hardware management application.

---

## 1. Production Deployment (via Docker)

This is the recommended method for running the application on a target system like Arch Linux. It ensures a consistent, self-contained environment.

### 1.1. Prerequisites

- **Git:** To clone the repository.
- **Docker:** The container runtime.
- **Docker Compose:** For orchestrating the application container.

Install on Arch Linux:
```bash
sudo pacman -S git docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
# Log out and log back in for the group change to take effect
```

### 1.2. Startup Commands

1.  **Clone the repository from GitHub (replace with your URL):**
    ```bash
    git clone https://github.com/your-username/your-repository.git
    cd your-repository
    ```

2.  **Build the Docker image:**
    This command reads the `Dockerfile` and creates a container image with all dependencies.
    ```bash
    docker-compose build
    ```

3.  **Start the application container:**
    This command starts the application in detached mode (`-d`).
    ```bash
    docker-compose up -d
    ```

### 1.3. Management Commands

- **Check running containers:**
  ```bash
  docker ps
  ```
- **View application logs:**
  ```bash
  docker-compose logs -f
  ```
- **Stop the application:**
  ```bash
  docker-compose down
  ```

---

## 2. Interacting with the API (`curl`)

Once the application is running, you can use these `curl` commands from the host machine's terminal to interact with the API.

### 2.1. System & Hardware Status

- **Get System Health (Drives, RAID):**
  ```bash
  curl http://localhost:3177/api/system/health
  ```
- **Get NPU/Pi Status:**
  ```bash
  curl http://localhost:3177/api/npu/status
  ```

### 2.2. Power Control

- **Check Drive Array Power Status:**
  ```bash
  curl http://localhost:3177/api/power/array
  ```
- **Turn Drive Array Power OFF:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"state": "off"}' http://localhost:3177/api/power/array
  ```
- **Turn Drive Array Power ON:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"state": "on"}' http://localhost:3177/api/power/array
  ```

### 2.3. File System

- **Browse files in the root of the storage mock:**
  ```bash
  curl "http://localhost:3177/api/files/browse?path=/"
  ```
- **Create a new folder:**
  ```bash
  curl -X POST -H "Content-Type: application/json" -d '{"path": "new-folder"}' http://localhost:3177/api/files/folder
  ```

---

## 3. Local Development (Without Docker)

Use this method for actively developing the application code.

1.  **Set up the Python virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the development server:**
    The application will be accessible at `http://localhost:3177`.
    ```bash
    python3 main.py
    ```

---

## 4. Transitioning to Real Hardware

To move from the mock API to real hardware control, you will need to replace the `TODO` and `PRETENDING` sections in the code.

### 4.1. Power Control (Optocoupler)

- **File:** `main.py`
- **Function:** `power_array()`
- **Action:** Replace the `print(f"MOCK: ...")` line with code that controls the GPIO pin connected to your optocoupler. You would typically use a library like `RPi.GPIO` or a specific library for the Orange Pi's GPIO.

### 4.2. NPU Integration (Orange Pi)

- **File:** `npu_manager.py`
- **Functions:** `load_model()`, `unload_model()`, `run_inference()`
- **Action:** In each function, remove the `if IS_ORANGE_PI:` block that points to mock logic and uncomment/implement the `rknn` (RKNNLite) code. You will need to have the Rockchip Neural Network Toolkit libraries installed and correctly configured on your Arch Linux system for this to work.
