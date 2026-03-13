#!/bin/bash
# =================================================
# SmartGrow Cloudflare Tunnel Setup Script
# =================================================
# This script configures Cloudflare Tunnel for secure
# internet access to your Raspberry Pi SmartGrow server.
# =================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=========================================="
echo "   SmartGrow Cloudflare Tunnel Setup"
echo "=========================================="
echo -e "${NC}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Please run as root (sudo)${NC}"
    exit 1
fi

# Configuration
TUNNEL_NAME="${TUNNEL_NAME:-smartgrow}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
DOMAIN="${DOMAIN:-smartgrow.example.com}"

# Step 1: Install cloudflared
echo -e "${BLUE}Step 1: Installing cloudflared...${NC}"

# Detect architecture
ARCH=$(uname -m)
case $ARCH in
    aarch64|arm64)
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
        ;;
    armv7l|armhf)
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
        ;;
    x86_64)
        CLOUDFLARED_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
        ;;
    *)
        echo -e "${RED}Unsupported architecture: $ARCH${NC}"
        exit 1
        ;;
esac

if ! command -v cloudflared &> /dev/null; then
    echo "Downloading cloudflared for $ARCH..."
    curl -L -o /usr/local/bin/cloudflared $CLOUDFLARED_URL
    chmod +x /usr/local/bin/cloudflared
    echo -e "${GREEN}cloudflared installed successfully${NC}"
else
    echo -e "${GREEN}cloudflared already installed${NC}"
fi

# Verify installation
cloudflared --version

# Step 2: Authenticate with Cloudflare
echo -e "${BLUE}Step 2: Authenticating with Cloudflare...${NC}"
echo -e "${YELLOW}This will open a browser window. Please log in to your Cloudflare account.${NC}"
echo -e "${YELLOW}If you're running this on a headless Pi, copy the URL to another device.${NC}"

if [ ! -f ~/.cloudflared/cert.pem ]; then
    cloudflared tunnel login
    echo -e "${GREEN}Authentication successful${NC}"
else
    echo -e "${GREEN}Already authenticated${NC}"
fi

# Step 3: Create tunnel
echo -e "${BLUE}Step 3: Creating tunnel '${TUNNEL_NAME}'...${NC}"

# Check if tunnel exists
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' || true)

if [ -z "$TUNNEL_ID" ]; then
    cloudflared tunnel create $TUNNEL_NAME
    TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}')
    echo -e "${GREEN}Tunnel created with ID: $TUNNEL_ID${NC}"
else
    echo -e "${GREEN}Tunnel already exists with ID: $TUNNEL_ID${NC}"
fi

# Step 4: Create configuration file
echo -e "${BLUE}Step 4: Creating tunnel configuration...${NC}"

CONFIG_DIR="/etc/cloudflared"
mkdir -p $CONFIG_DIR

cat > $CONFIG_DIR/config.yml << EOF
# SmartGrow Cloudflare Tunnel Configuration
# Generated: $(date)

tunnel: $TUNNEL_ID
credentials-file: /root/.cloudflared/$TUNNEL_ID.json

# Ingress rules
ingress:
  # SmartGrow API server
  - hostname: $DOMAIN
    service: http://localhost:$LOCAL_PORT
    originRequest:
      noTLSVerify: true
      connectTimeout: 30s
      
  # WebSocket support for real-time updates
  - hostname: ws.$DOMAIN
    service: http://localhost:$LOCAL_PORT
    originRequest:
      httpHostHeader: localhost
      
  # Catch-all rule (required)
  - service: http_status:404

# Logging
loglevel: info
logfile: /var/log/cloudflared.log

# Metrics
metrics: localhost:2000
EOF

echo -e "${GREEN}Configuration created at $CONFIG_DIR/config.yml${NC}"

# Step 5: Set up DNS (manual step)
echo -e "${BLUE}Step 5: DNS Configuration${NC}"
echo -e "${YELLOW}Run the following command to configure DNS:${NC}"
echo ""
echo "  cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN"
echo ""
echo -e "${YELLOW}This will create a CNAME record pointing $DOMAIN to your tunnel.${NC}"

# Step 6: Create systemd service
echo -e "${BLUE}Step 6: Creating systemd service...${NC}"

cat > /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=Cloudflare Tunnel for SmartGrow
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=10

# Logging
StandardOutput=append:/var/log/cloudflared.log
StandardError=append:/var/log/cloudflared.log

# Security
ProtectSystem=full
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable cloudflared.service

echo -e "${GREEN}Systemd service created${NC}"

# Step 7: Start the tunnel
echo -e "${BLUE}Step 7: Starting Cloudflare Tunnel...${NC}"
systemctl start cloudflared.service

# Check status
sleep 3
if systemctl is-active --quiet cloudflared.service; then
    echo -e "${GREEN}Cloudflare Tunnel is running!${NC}"
else
    echo -e "${RED}Failed to start tunnel. Check logs:${NC}"
    echo "  journalctl -u cloudflared.service -f"
fi

# Summary
echo ""
echo -e "${GREEN}=========================================="
echo "   Setup Complete!"
echo "==========================================${NC}"
echo ""
echo "Tunnel Name: $TUNNEL_NAME"
echo "Tunnel ID:   $TUNNEL_ID"
echo "Domain:      $DOMAIN"
echo "Local Port:  $LOCAL_PORT"
echo ""
echo "Commands:"
echo "  - Start:   sudo systemctl start cloudflared"
echo "  - Stop:    sudo systemctl stop cloudflared"
echo "  - Status:  sudo systemctl status cloudflared"
echo "  - Logs:    sudo journalctl -u cloudflared -f"
echo ""
echo -e "${YELLOW}Don't forget to run the DNS command shown above!${NC}"
