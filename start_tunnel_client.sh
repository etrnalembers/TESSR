#!/bin/bash
# start_tunnel_client.sh
# This script runs on the REMOTE machine to connect to the Orange Pi.

# --- Configuration ---
# The IP address or hostname of your Orange Pi.
ORANGE_PI_IP="192.168.1.100" # <-- IMPORTANT: Change this to the IP displayed by the server script

# The port the Chisel server is listening on.
CHISEL_PORT=3517

# The local port on THIS machine that will be forwarded.
# Connecting your VNC client to localhost:5900 will tunnel it to the Orange Pi.
LOCAL_PORT=5900

# The remote port on the Orange Pi where the VNC server is running.
VNC_SERVER_PORT=5900

# --- Wait for Server ---
echo "----------------------------------------------------"
echo "   Waiting for Orange Pi signal on $ORANGE_PI_IP:$CHISEL_PORT   "
echo "----------------------------------------------------"

# We use `nc` (netcat) to check if the port is open.
# The loop continues until `nc` can successfully connect.
# -z: Zero-I/O mode (scanning).
# -v: Verbose.
# -w 1: Timeout of 1 second for the connection attempt.
while ! nc -zvw 1 $ORANGE_PI_IP $CHISEL_PORT &>/dev/null; do
    echo -n "."
    sleep 2
done

echo -e "\nSignal detected! Orange Pi is online and ready."


# --- Start Tunnel ---
# The Chisel forward definition: <LOCAL_PORT_ON_THIS_MACHINE>:<REMOTE_PORT_ON_PI>
FORWARD_DEFINITION="$LOCAL_PORT:$VNC_SERVER_PORT"

echo "Starting Chisel tunnel..."
echo "Forwarding traffic from localhost:$LOCAL_PORT to OrangePi:$VNC_SERVER_PORT"
echo "Open your VNC client (e.g., TightVNC) and connect to: localhost:$LOCAL_PORT"
echo "Press [Ctrl+C] to close the tunnel."

# Start the Chisel client
./tunnels/chisel_linux_amd64 client $ORANGE_PI_IP:$CHISEL_PORT $FORWARD_DEFINITION
