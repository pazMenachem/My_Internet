#!/bin/bash

# Stop all containers
docker-compose down

# Cleanup X server permissions
xhost -local:docker

echo "System stopped successfully!" 