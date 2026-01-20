# TRACK D - GCP Deployment Guide

Complete step-by-step guide to deploy TRACK D WebSocket server to Google Cloud Platform.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Create GCP VM Instance](#create-gcp-vm-instance)
3. [Deploy Code to VM](#deploy-code-to-vm)
4. [Configure Firewall](#configure-firewall)
5. [Start the Service](#start-the-service)
6. [Test Connection](#test-connection)
7. [Monitor & Manage](#monitor--manage)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### On Your Local Machine

✅ **Google Cloud SDK installed**
```bash
# Check if installed
gcloud --version

# If not installed, install from:
# https://cloud.google.com/sdk/docs/install
```

✅ **Authenticate with GCP**
```bash
gcloud auth login
```

✅ **Set your GCP project**
```bash
# List projects
gcloud projects list

# Set active project
gcloud config set project YOUR_PROJECT_ID
```

✅ **SSH keys configured** (automatic with gcloud)

---

## Step 1: Create GCP VM Instance

### Option A: Using GCP Console (Web UI)

1. **Go to Compute Engine** → VM Instances
2. **Click "Create Instance"**
3. **Configure:**

```
Name: trackd-server
Region: us-central1 (or your preferred region)
Zone: us-central1-a

Machine Configuration:
  Series: E2
  Machine type: e2-medium (2 vCPU, 4 GB memory)

Boot disk:
  Operating System: Ubuntu
  Version: Ubuntu 22.04 LTS
  Boot disk type: Standard persistent disk
  Size: 20 GB

Firewall:
  ☑ Allow HTTP traffic
  ☑ Allow HTTPS traffic
```

4. **Click "Create"**

### Option B: Using gcloud CLI (Recommended)

```bash
gcloud compute instances create trackd-server \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --tags=http-server,https-server
```

**Expected output:**
```
Created [https://www.googleapis.com/compute/v1/projects/YOUR_PROJECT/zones/us-central1-a/instances/trackd-server].
NAME           ZONE           MACHINE_TYPE  INTERNAL_IP  EXTERNAL_IP    STATUS
trackd-server  us-central1-a  e2-medium     10.128.0.2   34.123.45.67   RUNNING
```

**Note the EXTERNAL_IP** - you'll need this later!

---

## Step 2: Deploy Code to VM

### Method 1: Automated Deployment (Recommended)

**From your local machine:**

```bash
# Navigate to TRACK_D directory
cd /home/user/TRACK_D

# Make deploy script executable
chmod +x deploy.sh

# Copy files to VM
gcloud compute scp --recurse . trackd-server:/tmp/trackd --zone=us-central1-a

# SSH into VM and run deployment
gcloud compute ssh trackd-server --zone=us-central1-a --command="cd /tmp/trackd && chmod +x deploy.sh && ./deploy.sh"
```

This will:
- ✅ Update system packages
- ✅ Install Python and dependencies
- ✅ Set up virtual environment
- ✅ Install all Python packages
- ✅ Create systemd service
- ✅ Start the server

### Method 2: Manual Deployment

**Step 2.1: Copy files to VM**

```bash
# From local machine
cd /home/user/TRACK_D

# Copy entire directory to VM
gcloud compute scp --recurse . trackd-server:/tmp/trackd --zone=us-central1-a
```

**Step 2.2: SSH into VM**

```bash
gcloud compute ssh trackd-server --zone=us-central1-a
```

**Step 2.3: Set up on VM**

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
sudo apt-get install -y python3 python3-pip python3-venv git build-essential

# Create project directory
sudo mkdir -p /opt/trackd
sudo chown $USER:$USER /opt/trackd

# Move files
mv /tmp/trackd/* /opt/trackd/
cd /opt/trackd

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install -r requirements-cloud.txt

# Test server (Ctrl+C to stop)
python3 server_cloud.py
```

If it runs without errors, proceed to systemd setup.

**Step 2.4: Create systemd service**

```bash
# Create service file
sudo nano /etc/systemd/system/trackd.service
```

Paste this content (replace YOUR_USERNAME with your actual username):

```ini
[Unit]
Description=TRACK D Liveness Detection WebSocket Server
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/trackd
Environment="PATH=/opt/trackd/venv/bin"
ExecStart=/opt/trackd/venv/bin/python3 /opt/trackd/server_cloud.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/trackd/server.log
StandardError=append:/var/log/trackd/error.log

NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, Y, Enter)

**Step 2.5: Create log directory**

```bash
sudo mkdir -p /var/log/trackd
sudo chown $USER:$USER /var/log/trackd
```

**Step 2.6: Enable and start service**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (auto-start on boot)
sudo systemctl enable trackd

# Start service
sudo systemctl start trackd

# Check status
sudo systemctl status trackd
```

You should see:
```
● trackd.service - TRACK D Liveness Detection WebSocket Server
     Loaded: loaded (/etc/systemd/system/trackd.service; enabled)
     Active: active (running) since ...
```

---

## Step 3: Configure Firewall

### Allow WebSocket Port (8765)

**Using gcloud:**

```bash
# Create firewall rule
gcloud compute firewall-rules create allow-trackd-websocket \
    --allow=tcp:8765 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow WebSocket connections to TRACK D server"
```

**Or using GCP Console:**

1. Go to **VPC Network** → **Firewall**
2. Click **Create Firewall Rule**
3. Configure:
   ```
   Name: allow-trackd-websocket
   Direction: Ingress
   Action: Allow
   Targets: All instances in the network
   Source IP ranges: 0.0.0.0/0
   Protocols and ports: tcp:8765
   ```
4. Click **Create**

---

## Step 4: Start the Service

If you haven't already:

```bash
# SSH into VM
gcloud compute ssh trackd-server --zone=us-central1-a

# Start service
sudo systemctl start trackd

# Enable auto-start on boot
sudo systemctl enable trackd

# Check status
sudo systemctl status trackd
```

---

## Step 5: Test Connection

### Get Your VM's External IP

```bash
gcloud compute instances describe trackd-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

Example output: `34.123.45.67`

### Test from Local Machine

**Create test file** `test_cloud.html`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>Test TRACK D Cloud</title>
</head>
<body>
  <h1>TRACK D Cloud Test</h1>
  <div id="status">Connecting...</div>

  <script>
    const ws = new WebSocket('ws://34.123.45.67:8765');  // ← Your VM IP

    ws.onopen = () => {
      document.getElementById('status').textContent = '✓ Connected!';
      document.getElementById('status').style.color = 'green';
      console.log('Connected to TRACK D cloud server');
    };

    ws.onmessage = (event) => {
      console.log('Received:', event.data);
    };

    ws.onerror = (error) => {
      document.getElementById('status').textContent = '✗ Connection failed';
      document.getElementById('status').style.color = 'red';
      console.error('Error:', error);
    };
  </script>
</body>
</html>
```

Open in browser and check console.

### Test with curl

```bash
# Test if port is open
nc -zv 34.123.45.67 8765

# Or use telnet
telnet 34.123.45.67 8765
```

---

## Step 6: Monitor & Manage

### View Logs

```bash
# Real-time logs
sudo journalctl -u trackd -f

# Last 100 lines
sudo journalctl -u trackd -n 100

# View log files directly
tail -f /var/log/trackd/server.log
tail -f /var/log/trackd/error.log
```

### Service Management

```bash
# Check status
sudo systemctl status trackd

# Start
sudo systemctl start trackd

# Stop
sudo systemctl stop trackd

# Restart
sudo systemctl restart trackd

# Disable auto-start
sudo systemctl disable trackd

# Enable auto-start
sudo systemctl enable trackd
```

### Update Code

```bash
# From local machine - copy new files
gcloud compute scp server_cloud.py trackd-server:/opt/trackd/ --zone=us-central1-a

# SSH and restart
gcloud compute ssh trackd-server --zone=us-central1-a
cd /opt/trackd
source venv/bin/activate
sudo systemctl restart trackd
```

### Monitor Resources

```bash
# SSH into VM
gcloud compute ssh trackd-server --zone=us-central1-a

# CPU and memory usage
htop

# Or
top

# Disk usage
df -h

# Service resource usage
systemctl status trackd
```

---

## Step 7: Update Frontend

In your frontend code, update the WebSocket URL:

```javascript
// Before (local)
const SERVER_URL = 'ws://localhost:8765';

// After (cloud)
const SERVER_URL = 'ws://34.123.45.67:8765';  // Your VM's external IP
```

**For production, use domain name:**
```javascript
const SERVER_URL = 'wss://trackd.yourdomain.com:8765';  // With SSL
```

---

## Troubleshooting

### Server Won't Start

**Check logs:**
```bash
sudo journalctl -u trackd -n 50
```

**Common issues:**
- Python package missing → `source venv/bin/activate && pip install -r requirements-cloud.txt`
- Permission error → `sudo chown -R $USER:$USER /opt/trackd`
- Port already in use → `sudo lsof -i :8765`

### Can't Connect from Frontend

**Check firewall:**
```bash
# List firewall rules
gcloud compute firewall-rules list

# Check if port 8765 is allowed
gcloud compute firewall-rules describe allow-trackd-websocket
```

**Check if server is listening:**
```bash
# SSH into VM
sudo netstat -tlnp | grep 8765

# Or
sudo ss -tlnp | grep 8765
```

Should show:
```
tcp    0    0 0.0.0.0:8765    0.0.0.0:*    LISTEN    12345/python3
```

**Test from VM itself:**
```bash
# SSH into VM
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Host: localhost:8765" -H "Origin: http://localhost:8765" \
     http://localhost:8765
```

### High CPU/Memory Usage

**Monitor:**
```bash
# SSH into VM
top

# Or more detailed
htop
```

**If high, consider:**
- Upgrade to larger machine type
- Optimize frame processing rate
- Add rate limiting

**Upgrade machine type:**
```bash
# Stop VM
gcloud compute instances stop trackd-server --zone=us-central1-a

# Change machine type
gcloud compute instances set-machine-type trackd-server \
    --machine-type=e2-standard-2 \
    --zone=us-central1-a

# Start VM
gcloud compute instances start trackd-server --zone=us-central1-a
```

### Python Dependencies Issues

**If mediapipe or OpenCV fails:**

```bash
# SSH into VM
cd /opt/trackd
source venv/bin/activate

# Reinstall specific package
pip uninstall opencv-python-headless
pip install opencv-python-headless==4.8.1.78

# Or reinstall all
pip install --force-reinstall -r requirements-cloud.txt
```

---

## Cost Optimization

### Estimated Costs (us-central1)

**e2-medium (2 vCPU, 4 GB RAM):**
- Running 24/7: ~$24/month
- Running 8 hours/day: ~$8/month

**Network egress:**
- First 1 GB/month: Free
- 1-10 TB: $0.12/GB
- For typical usage: ~$5-20/month

**Total: ~$30-45/month** for 24/7 operation

### Cost Saving Tips

1. **Stop VM when not in use:**
   ```bash
   gcloud compute instances stop trackd-server --zone=us-central1-a
   ```

2. **Use preemptible VM** (cheaper but can be terminated):
   ```bash
   gcloud compute instances create trackd-server \
       --preemptible \
       ...other options...
   ```

3. **Use smaller machine for testing:**
   - e2-micro (free tier eligible): 2 vCPU, 1 GB RAM
   - Good for testing, may be slow for production

---

## Production Checklist

Before going to production:

- [ ] Server running and accessible
- [ ] Firewall configured (port 8765 open)
- [ ] Systemd service enabled (auto-start on boot)
- [ ] Logs rotating properly
- [ ] Frontend tested and working
- [ ] SSL/TLS configured (wss://)
- [ ] Domain name configured (optional)
- [ ] Monitoring set up
- [ ] Backups configured (if saving results)
- [ ] Load testing completed
- [ ] Error handling tested
- [ ] Documentation updated

---

## Next Steps

1. ✅ Deploy server to GCP (this guide)
2. ✅ Configure firewall
3. ✅ Update frontend with VM IP
4. ⏭️ Test end-to-end flow
5. ⏭️ Set up domain name (optional)
6. ⏭️ Configure SSL/TLS for wss://
7. ⏭️ Add authentication (if needed)
8. ⏭️ Set up monitoring/alerting

---

## SSL/TLS Setup (Optional but Recommended)

For production, use secure WebSocket (wss://):

### 1. Get Domain Name

Point domain to VM IP:
```
trackd.yourdomain.com → 34.123.45.67
```

### 2. Get SSL Certificate

```bash
# Install certbot
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d trackd.yourdomain.com
```

### 3. Update Server Code

Modify `server_cloud.py`:

```python
import ssl

# Create SSL context
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(
    '/etc/letsencrypt/live/trackd.yourdomain.com/fullchain.pem',
    '/etc/letsencrypt/live/trackd.yourdomain.com/privkey.pem'
)

# Use in websockets.serve()
async with websockets.serve(
    server.handle_client,
    WEBSOCKET_HOST,
    WEBSOCKET_PORT,
    ssl=ssl_context
):
    await asyncio.Future()
```

### 4. Update Frontend

```javascript
const SERVER_URL = 'wss://trackd.yourdomain.com:8765';  // wss instead of ws
```

---

## Support

**Logs Location:**
- Server log: `/var/log/trackd/server.log`
- Error log: `/var/log/trackd/error.log`
- System log: `sudo journalctl -u trackd`

**Useful Commands:**
```bash
# View real-time logs
sudo journalctl -u trackd -f

# Check if server is running
sudo systemctl status trackd

# Test connection
nc -zv VM_IP 8765
```

---

## Summary

**What We Did:**
1. ✅ Created GCP VM instance (Ubuntu 22.04)
2. ✅ Deployed TRACK D server code
3. ✅ Set up Python virtual environment
4. ✅ Installed dependencies
5. ✅ Created systemd service
6. ✅ Configured firewall
7. ✅ Started server
8. ✅ Tested connection

**Your Server is Now Running at:**
```
ws://YOUR_VM_EXTERNAL_IP:8765
```

**Frontend Team Can:**
- Connect to WebSocket
- Send camera frames
- Receive liveness detection results

---

🎉 **Deployment Complete!** Your TRACK D server is live on GCP! 🚀
