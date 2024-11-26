#!/bin/bash

# Flush existing NAT table rules to start fresh
sudo iptables -t nat -F

echo "Redirecting DNS traffic to AdGuard (94.140.14.14)..."

# Redirect UDP DNS traffic to 94.140.14.14
sudo iptables -t nat -A OUTPUT -p udp --dport 53 -j DNAT --to-destination 94.140.14.14

# Masquerade (SNAT) the outgoing packets to ensure proper routing
sudo iptables -t nat -A POSTROUTING -p udp --dport 53 -d 94.140.14.14 -j MASQUERADE

echo "DNS traffic is now being redirected to AdGuard (94.140.14.14)."

# Display the applied rules
echo "Current iptables NAT rules:"
sudo iptables -t nat -L -n -v