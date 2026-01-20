#!/bin/bash

#############################################
# TRACK D - GCP Deployment Script
# Automated deployment to Google Cloud VM
#############################################

set -e  # Exit on error

echo "=============================================="
echo "    TRACK D - GCP Deployment Script"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/opt/trackd"
SERVICE_USER="trackd"
SERVICE_NAME="trackd"

echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt-get update
sudo apt-get upgrade -y

echo -e "${GREEN}[2/8] Installing Python and dependencies...${NC}"
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    python3-opencv

echo -e "${GREEN}[3/8] Creating project directory...${NC}"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

echo -e "${GREEN}[4/8] Copying project files...${NC}"
cp -r . $PROJECT_DIR/
cd $PROJECT_DIR

echo -e "${GREEN}[5/8] Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${GREEN}[6/8] Installing Python packages...${NC}"
# Install packages without camera/GUI dependencies
pip install --upgrade pip
pip install numpy==1.24.3
pip install websockets==12.0
pip install mediapipe==0.10.9

# Install OpenCV headless (no GUI, smaller footprint)
pip install opencv-python-headless==4.8.1.78

echo -e "${GREEN}[7/8] Creating systemd service...${NC}"
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=TRACK D Liveness Detection WebSocket Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/server_cloud.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trackd/server.log
StandardError=append:/var/log/trackd/error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}[8/8] Setting up logging...${NC}"
sudo mkdir -p /var/log/trackd
sudo chown $USER:$USER /var/log/trackd

echo -e "${GREEN}Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

echo ""
echo "=============================================="
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo "=============================================="
echo ""
echo "Service Status:"
sudo systemctl status ${SERVICE_NAME} --no-pager
echo ""
echo "Useful commands:"
echo "  Check status:  sudo systemctl status ${SERVICE_NAME}"
echo "  View logs:     sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Restart:       sudo systemctl restart ${SERVICE_NAME}"
echo "  Stop:          sudo systemctl stop ${SERVICE_NAME}"
echo ""
echo "Server is running on ws://0.0.0.0:8765"
echo ""
echo "Next steps:"
echo "  1. Configure firewall to allow port 8765"
echo "  2. Update frontend with server IP address"
echo "  3. Test connection from frontend"
echo ""
