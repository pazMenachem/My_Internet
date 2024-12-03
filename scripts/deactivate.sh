#!/bin/bash

# Exit on any error
set -e

echo "Starting deactivation process..."

# Get module name at startup
MODULE_NAME=$(grep "define MODULE_NAME" "$(pwd)/kernel/src/utils.h" 2>/dev/null | cut -d'"' -f2)
if [ -z "$MODULE_NAME" ]; then
    echo "Error: Could not fetch module name from /kernel/src/utils.h"
    exit 1
fi

# Function to check if the kernel module is loaded
check_module() {
    if lsmod | grep -q "^${MODULE_NAME}"; then
        return 0
    else
        return 1
    fi
}

# Kill client process if it exists
if [ -f .client.pid ]; then
    echo "Stopping client..."
    kill $(cat .client.pid) 2>/dev/null || true
    rm .client.pid
fi

# Remove kernel module if loaded
if check_module; then
    echo "Removing kernel module..."
    cd kernel
    if ! make remove; then
        echo "Warning: Failed to remove kernel module"
    fi
    cd ..
fi

# Kill server process if it exists
if [ -f .server.pid ]; then
    echo "Stopping server..."
    kill $(cat .server.pid) 2>/dev/null || true
    rm .server.pid
fi

# Call reset_dns.sh
echo "Resetting DNS settings..."
./scripts/reset_dns.sh

echo "System deactivated successfully!" 