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

2.  **Start the Mock container (For Development/PC):**
    This builds the `mock-env` profile, completely sandboxed from physical hardware.
    ```bash
    docker compose --profile dev up -d --build
    ```

3.  **Start the Real container (For Orange Pi/Production):**
    This builds the `real-env` profile with `privileged` access to toggle GPIO pins.
    ```bash
    docker compose --profile prod up -d --build
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

## 4. Hardware Wiring & Optocoupler Architecture

TESSR utilizes a **4N35 Optocoupler** to isolate the Orange Pi's logic board from the 300W PSU's high-current potential preventing backwash inductive loads.

### 4.1. 4N35 Wiring Instructions
- **Trigger End (Orange Pi):**
  - **Pin 17 (3.3V+)**: Needs to be wired to the 4N35 Anode (Pin 1) with an appropriate current-limiting resistor.
  - **Pin 20 (GND)**: Wire to the 4N35 Cathode (Pin 2).
  - *Note: Ensure your `PSU_GPIO_PIN` env var points to the software-switchable GPIO number that supplies the 3.3V+ logic.*
- **Acceptor End (PSU):**
  - Uses isolated grounds on the PSU polarity acceptor, triggered via its own motherboard headers.
  - Connect the ATX **PS_ON# (Green wire)** to the Collector (Pin 5) and the ATX **GND (Black wire)** to the Emitter (Pin 4).
- **Logic Level:** Sending a `HIGH` (1) to the GPIO turns the PSU **ON**.

### 4.2. Troubleshooting the Optocoupler
1. Connect a multimeter in continuity mode across the 4N35 Collector (Pin 5) and Emitter (Pin 4) *without* the PSU attached.
2. Ensure you are running the `prod` Docker profile on the Orange Pi.
3. Trigger the PSU via the testing command:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"state": "on"}' http://localhost:3177/api/power/array
   ```
4. **Expected Result:** Multimeter should beep (closed circuit).
5. Trigger it off:
   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"state": "off"}' http://localhost:3177/api/power/array
   ```
6. **Expected Result:** Multimeter stops beeping (open circuit).
7. If it fails: Verify `/sys/class/gpio/` has correctly exported the pin designated in `PSU_GPIO_PIN`.

### 4.3. Simulating Fault Scenarios
You can dry-run emergency fallbacks to verify the container handles sudden active-low shutdowns:
- **Power Surge Mock:** `curl -X POST -H "Content-Type: application/json" -d '{"state": "power_surge"}' http://localhost:3177/api/power/array`
- **Power Loss Mock:** `curl -X POST -H "Content-Type: application/json" -d '{"state": "power_loss"}' http://localhost:3177/api/power/array`
