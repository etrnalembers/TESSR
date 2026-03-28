#!/bin/bash
# start_tunnel_server.sh
# This script displays the IP address for SSH tunneling.

# --- Get and Display IP ---
# Find the primary IP address of the Orange Pi
IP_ADDR=$(hostname -I | awk '{print $1}')

if [ -z "$IP_ADDR" ]; then
    echo "Error: Could not determine IP address." >&2
    exit 1
fi

clear
echo "=================================================="
echo "      Orange Pi SSH Tunnel Information      "
echo "=================================================="
echo
echo "My IP Address is: $IP_ADDR"
echo
echo "Use this IP address in the 'start_tunnel_client.sh' script on your remote machine."
echo "Ensure the SSH server is running on this device (sudo systemctl enable --now ssh)."
echo
