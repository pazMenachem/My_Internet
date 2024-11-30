#!/bin/bash

# Allow X server connections for GUI
xhost +local:docker

# Build and start containers
docker-compose up -d

# Wait for ubuntu container to be ready
echo "Waiting for ubuntu container to be ready..."
sleep 5

# Build and install kernel module
docker exec ubuntu_base /usr/local/bin/kernel_setup.sh

# Show status
docker-compose ps

echo "System started successfully!" 