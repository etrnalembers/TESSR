#!/bin/bash
# generate_ssh_keys.sh
# This script generates an SSH key pair for connecting to the Orange Pi.

KEY_PATH="$HOME/.ssh/orange_pi_key"

echo "--- SSH Key Pair Generation ---"

if [ -f "$KEY_PATH" ]; then
    echo "An SSH key already exists at $KEY_PATH."
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Key generation aborted. The existing key will be used."
        echo "------------------------------------------------"
        exit 0
    fi
fi

echo "Generating a new 4096-bit RSA key pair."
# -t rsa: specifies the type of key to create
# -b 4096: specifies the number of bits in the key
# -f "$KEY_PATH": specifies the filename of the key file
# -N "": specifies an empty passphrase for convenience
ssh-keygen -t rsa -b 4096 -f "$KEY_PATH" -N ""

echo ""
echo "Key pair generated successfully!"
echo "Private Key: $KEY_PATH"
echo "Public Key:  $KEY_PATH.pub"
echo ""
echo "--- IMPORTANT NEXT STEP ---"
echo "You now MUST copy the public key to your Orange Pi."
echo "Please run the following command from this terminal, replacing '<user>' and '<orange-pi-ip>' with your details:"
echo ""
echo "ssh-copy-id -i $KEY_PATH.pub <user>@<orange-pi-ip>"
echo ""
echo "After you run that command, you can use 'start_tunnel_client.sh' to connect without a password."
echo "------------------------------------------------"
