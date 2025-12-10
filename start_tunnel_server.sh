#!/bin/bash
# start_tunnel_server.sh
# This script starts the Chisel server on the Orange Pi.

# --- Configuration ---
CHISEL_PORT=3517
VNC_PORT=5900

# --- Get and Display IP ---
# Find the primary IP address of the Orange Pi
IP_ADDR=$(hostname -I | awk '{print $1}')

if [ -z "$IP_ADDR" ]; then
    echo "Error: Could not determine IP address." >&2
    exit 1
fi

clear
echo "=================================================="
echo "      Orange Pi Chisel Tunnel Server      "
echo "=================================================="
echo
echo "My IP Address is: $IP_ADDR"
echo "Use this IP in the 'start_tunnel_client.sh' script on your remote machine."
echo
echo "Listening for client connections on port: $CHISEL_PORT..."
echo "Press [Ctrl+C] to stop the server."
echo

# Start the Chisel server
./tunnels/chisel_linux_arm64 server --port $CHISEL_PORT --reverse
