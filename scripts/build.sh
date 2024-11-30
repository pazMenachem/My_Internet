#!/bin/bash

# Make all scripts executable
chmod +x scripts/*

# Force rebuild all images from scratch
docker-compose build --no-cache

# Alternative: rebuild specific service
if [ "$1" ]; then
    docker-compose build --no-cache "$1"
    echo "Rebuilt $1 service"
fi

echo "Build completed!" 