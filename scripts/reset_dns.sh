#!/bin/bash

# Flush all NAT table rules
sudo iptables -t nat -F

# Disable routing for localhost after the script completes
sudo sysctl -w net.ipv4.conf.all.route_localnet=0

echo "DNS redirection rules have been reset."

# Display the current (empty) rules
echo "Current iptables NAT rules:"
sudo iptables -t nat -L -n -v