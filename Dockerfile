# --- Base Stage ---
# Setting up standard python env
FROM python:3.10-slim as base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3177

# --- Mock Environment Stage ---
# Used for local development and sandbox simulation
FROM base as mock-env
# Default to running Gunicorn (mock mode depends on hardware check auto-failing)
CMD ["gunicorn", "--bind", "0.0.0.0:3177", "main:app"]

# --- Real Environment Stage ---
# Used for Orange Pi deployment, toggling physical GPIOs
FROM base as real-env
# Here you would install additional hardware dependencies if needed.
# Sysfs mapping doesn't strictly need extra pip packages, but if libgpiod is attached later:
# RUN apt-get update && apt-get install -y gpiod
CMD ["gunicorn", "--bind", "0.0.0.0:3177", "main:app"]
