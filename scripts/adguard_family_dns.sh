#!/bin/bash

# Enable routing for localhost
sudo sysctl -w net.ipv4.conf.all.route_localnet=1

# Flush existing NAT table rules to start fresh
sudo iptables -t nat -F

echo "Redirecting DNS traffic to AdGuard Family (94.140.14.15)..."

# Redirect UDP DNS traffic to 94.140.14.15
sudo iptables -t nat -A OUTPUT -p udp --dport 53 -j DNAT --to-destination 94.140.14.15

# Masquerade (SNAT) the outgoing packets to ensure proper routing
sudo iptables -t nat -A POSTROUTING -p udp --dport 53 -d 94.140.14.15 -j MASQUERADE

echo "DNS traffic is now being redirected to AdGuard Family (94.140.14.15)."

# Display the applied rules
echo "Current iptables NAT rules:"
sudo iptables -t nat -L -n -v 