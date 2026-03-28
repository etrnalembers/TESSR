#!/bin/bash
# start_tunnel_client.sh
# This script runs on the REMOTE machine to create a secure SSH tunnel to the Orange Pi.

# --- Configuration ---
LOCAL_PORT=5900
VNC_SERVER_PORT=5900
SSH_PORT=22
KEY_PATH="$HOME/.ssh/orange_pi_key"

# --- Pre-flight Check ---
if [ ! -f "$KEY_PATH" ]; then
    echo "Error: SSH private key not found at $KEY_PATH."
    echo "Please run the 'generate_ssh_keys.sh' script first to create one."
    exit 1
fi

# --- User Input ---
read -p "Enter the IP address of the Orange Pi: " ORANGE_PI_IP
read -p "Enter your SSH username for the Orange Pi (e.g., 'pi' or 'orangepi'): " SSH_USER

if [[ -z "$ORANGE_PI_IP" || -z "$SSH_USER" ]]; then
    echo "Error: IP address and username cannot be empty." >&2
    exit 1
fi

# --- Wait for SSH Server ---
echo "----------------------------------------------------"
echo "   Pinging the Orange Pi at $ORANGE_PI_IP... "
echo "----------------------------------------------------"

if ! ping -c 3 "$ORANGE_PI_IP" &>/dev/null; then
    echo "Error: The Orange Pi at $ORANGE_PI_IP is not reachable."
    exit 1
fi

echo "Orange Pi is online."
echo "----------------------------------------------------"
echo "   Waiting for SSH service on $ORANGE_PI_IP:$SSH_PORT   "
echo "----------------------------------------------------"

while ! nc -zvw 1 "$ORANGE_PI_IP" "$SSH_PORT" &>/dev/null; do
    echo -n "."
    sleep 2
done

echo -e "\nSSH service is active!"

# --- Start SSH Tunnel ---
FORWARD_SPEC="L$LOCAL_PORT:localhost:$VNC_SERVER_PORT"

echo "Creating SSH tunnel using the key at $KEY_PATH..."
echo "Forwarding traffic from localhost:$LOCAL_PORT to OrangePi:$VNC_SERVER_PORT"
echo "Open your VNC client and connect to: localhost:$LOCAL_PORT"
echo "Press [Ctrl+C] in this terminal to close the tunnel."
echo ""

# The -i flag specifies the identity file (private key) to use.
ssh -N -i "$KEY_PATH" -L "$FORWARD_SPEC" "$SSH_USER@$ORANGE_PI_IP"

echo "Tunnel closed."
