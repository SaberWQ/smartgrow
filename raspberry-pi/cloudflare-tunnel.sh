#!/bin/bash
# SmartGrow - Cloudflare Tunnel Setup
# Provides secure internet access to your greenhouse

echo "╔═══════════════════════════════════════╗"
echo "║  SmartGrow Cloudflare Tunnel Setup    ║"
echo "╚═══════════════════════════════════════╝"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo ./cloudflare-tunnel.sh)"
    exit 1
fi

# Install cloudflared
echo "[1/4] Installing Cloudflare Tunnel..."
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Verify installation
cloudflared --version

echo ""
echo "[2/4] Starting quick tunnel..."
echo "This will create a temporary public URL for your SmartGrow server."
echo ""
echo "Press Ctrl+C to stop the tunnel."
echo ""

# Start tunnel
cloudflared tunnel --url http://localhost:8000

# For permanent tunnel, create service:
# cloudflared service install
# cloudflared tunnel create smartgrow
# cloudflared tunnel route dns smartgrow smartgrow.yourdomain.com
