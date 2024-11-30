#!/bin/bash

cd /kernel
make clean
make
insmod my_internet.ko

# Check if module loaded successfully
if lsmod | grep -q "my_internet"; then
    echo "Kernel module loaded successfully"
else
    echo "Failed to load kernel module"
    exit 1
fi 