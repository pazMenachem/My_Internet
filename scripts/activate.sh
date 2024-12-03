#!/bin/bash

# Exit on any error
set -e

# Get module name at startup
MODULE_NAME=$(grep "define MODULE_NAME" "$(pwd)/kernel/src/utils.h" 2>/dev/null | cut -d'"' -f2)
if [ -z "$MODULE_NAME" ]; then
    echo "Error: Could not fetch module name from /kernel/src/utils.h"
    exit 1
fi

# Check if the kernel module is loaded
check_module() {
    if lsmod | grep -q "^${MODULE_NAME}"; then
        return 0
    else
        return 1
    fi
}

# Cleanup processes
cleanup() {
    echo "Cleaning up processes..."
    if [ -f .server.pid ]; then
        kill $(cat .server.pid) 2>/dev/null || true
        rm .server.pid
    fi
    if [ -f .client.pid ]; then
        kill $(cat .client.pid) 2>/dev/null || true
        rm .client.pid
    fi
}

# Set trap to cleanup on script failure
trap cleanup ERR

# Start the server
start_server() {
    echo "Starting server..."
    source venv/bin/activate
    python3 server/main.py &
    SERVER_PID=$!
    echo $SERVER_PID > .server.pid
    deactivate
    
    # Check if server started successfully (wait a few seconds and check if process exists)
    sleep 2
    if ! kill -0 $SERVER_PID 2>/dev/null; then
        echo "Error: Server failed to start"
        cleanup
        exit 1
    fi
}

# Start the client
start_client() {
    echo "Starting client..."
    source venv/bin/activate
    python3 client/main.py &
    CLIENT_PID=$!
    echo $CLIENT_PID > .client.pid
    deactivate
    
    # Check if client started successfully
    sleep 2
    if ! kill -0 $CLIENT_PID 2>/dev/null; then
        echo "Error: Client failed to start"
        cleanup
        exit 1
    fi
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
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
    
    cd "$PROJECT_ROOT/kernel"
    if ! make install; then
        echo "Error: Failed to load kernel module"
        cd "$PROJECT_ROOT"
        cleanup
        exit 1
    fi
    cd "$PROJECT_ROOT"
fi
sleep 1  # Wait for kernel module to initialize

# Start the client
start_client

echo "System activated successfully!"
echo "To deactivate, run: kill \$(cat .server.pid) \$(cat .client.pid)"
