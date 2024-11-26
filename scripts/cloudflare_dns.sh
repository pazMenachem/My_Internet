#!/bin/bash

# Flush existing NAT table rules to start fresh
sudo iptables -t nat -F

echo "Redirecting DNS traffic to Cloudflare (1.1.1.3)..."

# Redirect UDP DNS traffic to 1.1.1.3
sudo iptables -t nat -A OUTPUT -p udp --dport 53 -j DNAT --to-destination 1.1.1.3

# Masquerade (SNAT) the outgoing packets to ensure proper routing
sudo iptables -t nat -A POSTROUTING -p udp --dport 53 -d 1.1.1.3 -j MASQUERADE

echo "DNS traffic is now being redirected to Cloudflare (1.1.1.3)."

# Display the applied rules
echo "Current iptables NAT rules:"
sudo iptables -t nat -L -n -v