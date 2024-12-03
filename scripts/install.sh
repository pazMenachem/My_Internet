#!/bin/bash

# Exit on any error
set -e

echo "Starting installation process..."

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required commands
for cmd in python3 pip make gcc; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd is required but not installed."
        exit 1
    fi
done

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Install Python packages
echo "Installing Python packages..."

# Install requirements
if [ -f "./requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
fi

# Install the packages in development mode
echo "Installing packages in development mode..."
./venv/bin/pip install -e .

# Build and install kernel module
echo "Building kernel module..."
cd kernel
make clean
make

echo "Installation completed successfully!"
