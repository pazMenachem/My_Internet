#!/bin/bash

# Exit on any error
set -e

# Function to check if the kernel module is loaded
check_module() {
    if lsmod | grep -q "^my_internet"; then
        return 0
    else
        return 1
    fi
}

# Function to start the server
start_server() {
    echo "Starting server..."
    source venv/bin/activate
    python3 server/main.py &
    SERVER_PID=$!
    echo $SERVER_PID > .server.pid
    deactivate
}

# Function to start the client
start_client() {
    echo "Starting client..."
    source venv/bin/activate
    python3 client/main.py &
    CLIENT_PID=$!
    echo $CLIENT_PID > .client.pid
    deactivate
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Start server first
start_server
sleep 2  # Wait for server to initialize

# Load kernel module if not loaded
if ! check_module; then
    echo "Loading kernel module..."
    cd kernel
    sudo make install
    cd ..
fi
sleep 1  # Wait for kernel module to initialize

# Finally start the client
start_client

echo "System activated successfully!"
echo "To deactivate, run: kill \$(cat .server.pid) \$(cat .client.pid)"
