import os
import time
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default GPIO pin (can be overridden by environment variable)
# Note: Route matches Dell L305P-01 pinout where PS_ON is Pin 16 and adjacent GNDs are used.
# Ensure this maps to a valid switchable GPIO pin number (e.g. GPIO 16) for your specific board.
PSU_GPIO_PIN = os.environ.get("PSU_GPIO_PIN", "16")
SYSFS_GPIO_BASE = "/sys/class/gpio"

def export_gpio(pin):
    """Exports the GPIO pin to user space if not already exported."""
    gpio_dir = os.path.join(SYSFS_GPIO_BASE, f"gpio{pin}")
    if not os.path.exists(gpio_dir):
        try:
            with open(os.path.join(SYSFS_GPIO_BASE, "export"), "w") as f:
                f.write(str(pin))
            # Give the system a fraction of a second to create the directories
            time.sleep(0.1)
            logging.info(f"Exported GPIO pin {pin}.")
        except Exception as e:
            logging.error(f"Failed to export GPIO {pin}: {e}")
            return False
    return True

def set_direction(pin, direction="out"):
    """Sets the direction of the GPIO pin ('in' or 'out')."""
    direction_file = os.path.join(SYSFS_GPIO_BASE, f"gpio{pin}", "direction")
    try:
        with open(direction_file, "w") as f:
            f.write(direction)
        return True
    except Exception as e:
        logging.error(f"Failed to set direction for GPIO {pin}: {e}")
        return False

def set_value(pin, value):
    """
    Sets the value of the GPIO pin ('1' for HIGH, '0' for LOW).
    For a 4N35 optocoupler:
    - value '1' (HIGH) -> 3.3V logic -> turns ON internal LED -> closes phototransistor -> pulls Dell L305P-01 PS_ON (Pin 16) to adjacent GND -> turns ON PSU.
    - value '0' (LOW) -> 0V logic -> turns OFF internal LED -> opens phototransistor -> PS_ON (Pin 16) floats High -> turns OFF PSU.
    (Active low logic on the Pi side is only used for emergency fallbacks)
    """
    value_file = os.path.join(SYSFS_GPIO_BASE, f"gpio{pin}", "value")
    try:
        with open(value_file, "w") as f:
            f.write(str(value))
        logging.info(f"Set GPIO {pin} to value {value}.")
        return True
    except Exception as e:
        logging.error(f"Failed to write value {value} to GPIO {pin}: {e}")
        return False

def initialize():
    """Sets up the GPIO pin for the PSU optocoupler."""
    if export_gpio(PSU_GPIO_PIN):
        set_direction(PSU_GPIO_PIN, "out")
        logging.info("PSU GPIO controller initialized successfully.")

def turn_on_psu():
    """Activates the optocoupler to turn on the Dell L305P-01 PSU."""
    logging.info("Triggering PSU ON via 4N35 Optocoupler...")
    return set_value(PSU_GPIO_PIN, 1)

def turn_off_psu():
    """Deactivates the optocoupler to turn off the Dell L305P-01 PSU."""
    logging.info("Triggering PSU OFF via 4N35 Optocoupler...")
    return set_value(PSU_GPIO_PIN, 0)

def trigger_emergency_fallback():
    """
    If 12V, 5V, or data rails fail and the Orange Pi has sufficient time to react,
    this initiates an active-low/emergency shutdown routine to protect the array.
    """
    logging.warning("EMERGENCY FALLBACK: Cutting PSU and locking state.")
    # In a true hardware emergency, ensure the signal is physically grounded
    return set_value(PSU_GPIO_PIN, 0)
