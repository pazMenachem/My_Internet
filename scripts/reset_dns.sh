#!/bin/bash

# Flush all NAT table rules
sudo iptables -t nat -F

echo "DNS redirection rules have been reset."

# Display the current (empty) rules
echo "Current iptables NAT rules:"
sudo iptables -t nat -L -n -v