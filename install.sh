#!/bin/bash

# This script sets up the Python virtual environment and installs dependencies.

echo "Creating Python virtual environment in ./.venv..."
python3 -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "----------------------------------------------------"
echo "Installation complete!"
echo "To activate the virtual environment in your shell, run:"
echo "source .venv/bin/activate"
echo "----------------------------------------------------"

