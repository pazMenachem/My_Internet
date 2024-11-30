FROM ubuntu:22.04

# Install basic build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /kernel

# Entry point will be handled by docker-compose