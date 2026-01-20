# 🚀 TRACK D - Cloud Deployment Ready!

## What We Built

You now have **TWO versions** of the TRACK D server:

### 1. **Local Version** (`server.py`)
- For local testing with physical camera
- Server captures camera directly
- Test client included

### 2. **Cloud Version** (`server_cloud.py`) ⭐
- For GCP deployment (no camera needed on server)
- Frontend captures camera in browser
- Sends frames to cloud server
- Perfect for production!

---

## 📦 New Files Created

| File | Purpose |
|------|---------|
| `server_cloud.py` | Cloud WebSocket server (receives frames from frontend) |
| `deploy.sh` | Automated GCP deployment script |
| `trackd.service` | Systemd service template |
| `requirements-cloud.txt` | Cloud-optimized Python dependencies |
| `GCP_DEPLOYMENT_GUIDE.md` | Complete step-by-step deployment guide |
| `FRONTEND_CLOUD_INTEGRATION.md` | Frontend integration with camera examples |

---

## 🎯 Quick Start: Deploy to GCP in 5 Minutes

### Step 1: Create GCP VM

```bash
gcloud compute instances create trackd-server \
    --zone=us-central1-a \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --tags=http-server,https-server
```

### Step 2: Copy Files to VM

```bash
cd /home/user/TRACK_D

# Copy all files
gcloud compute scp --recurse . trackd-server:/tmp/trackd --zone=us-central1-a
```

### Step 3: Deploy (Automated)

```bash
# SSH and run deployment script
gcloud compute ssh trackd-server --zone=us-central1-a --command="cd /tmp/trackd && chmod +x deploy.sh && ./deploy.sh"
```

### Step 4: Configure Firewall

```bash
# Allow WebSocket port 8765
gcloud compute firewall-rules create allow-trackd-websocket \
    --allow=tcp:8765 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow WebSocket connections to TRACK D server"
```

### Step 5: Get Your Server IP

```bash
gcloud compute instances describe trackd-server \
    --zone=us-central1-a \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

**Example output:** `34.123.45.67`

---

## 🌐 Update Frontend

In your frontend code:

```javascript
// Connect to your cloud server
const ws = new WebSocket('ws://34.123.45.67:8765');  // ← Your VM IP

// Start analysis
ws.send(JSON.stringify({ command: 'START_ANALYSIS' }));

// Capture camera
const stream = await navigator.mediaDevices.getUserMedia({
  video: { width: 800, height: 600 }
});

// Send frames (10 FPS)
setInterval(() => {
  // Draw video to canvas
  ctx.drawImage(video, 0, 0);

  // Convert to base64
  const frameData = canvas.toDataURL('image/jpeg', 0.8);

  // Send to server
  ws.send(JSON.stringify({
    type: 'frame',
    frame: frameData
  }));
}, 100);  // 10 FPS

// Receive results
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Status:', data.status);
  console.log('Confidence:', data.confidence);

  if (data.result === 'LIVE') {
    console.log('✓ Real finger detected!');
  } else if (data.result === 'SPOOF') {
    console.log('✗ Attack detected:', data.attack_type);
  }
};
```

**See complete examples in:** `FRONTEND_CLOUD_INTEGRATION.md`

---

## 📚 Documentation Files

### For You (DevOps/Backend)

1. **`GCP_DEPLOYMENT_GUIDE.md`** - Read this first!
   - Complete deployment walkthrough
   - Firewall configuration
   - SSL/TLS setup
   - Monitoring and troubleshooting
   - Cost optimization

2. **`deploy.sh`** - Automated deployment script
   - Sets up everything automatically
   - Creates systemd service
   - Configures logging

3. **`trackd.service`** - Systemd service template
   - Auto-start on boot
   - Auto-restart on crash
   - Production-ready

### For Frontend Team

1. **`FRONTEND_CLOUD_INTEGRATION.md`** - Give this to frontend!
   - Complete integration guide
   - Vanilla JavaScript example
   - React example
   - Camera capture code
   - Frame sending logic
   - Result handling

---

## 🔥 Key Differences: Local vs Cloud

| Feature | Local (`server.py`) | Cloud (`server_cloud.py`) |
|---------|---------------------|---------------------------|
| **Camera** | Server captures | Frontend captures |
| **Frame Flow** | Server → Frontend | Frontend → Server |
| **Use Case** | Local testing | Production deployment |
| **Camera Required** | Yes (on server) | No (browser camera) |
| **Best For** | Development | Cloud deployment |

---

## ✅ Testing Checklist

- [ ] GCP VM created
- [ ] Files deployed to VM
- [ ] Deployment script ran successfully
- [ ] Service running: `sudo systemctl status trackd`
- [ ] Firewall configured (port 8765 open)
- [ ] Server accessible from external IP
- [ ] Frontend updated with server IP
- [ ] Camera permission granted in browser
- [ ] Frames sending to server
- [ ] Results received from server
- [ ] Auto-restart working (after 3 seconds)
- [ ] Multiple verification rounds working

---

## 🛠️ Useful Commands

### Check Server Status
```bash
# SSH into VM
gcloud compute ssh trackd-server --zone=us-central1-a

# Check service status
sudo systemctl status trackd

# View logs (real-time)
sudo journalctl -u trackd -f

# View log files
tail -f /var/log/trackd/server.log
```

### Restart Server
```bash
sudo systemctl restart trackd
```

### Update Code
```bash
# From local machine
gcloud compute scp server_cloud.py trackd-server:/opt/trackd/ --zone=us-central1-a

# SSH and restart
gcloud compute ssh trackd-server --zone=us-central1-a
sudo systemctl restart trackd
```

---

## 💰 Estimated Costs

**GCP VM (e2-medium, us-central1):**
- 24/7 operation: ~$24/month
- Network egress: ~$5-20/month
- **Total: ~$30-45/month**

**Cost saving:**
- Stop VM when not in use
- Use smaller machine for testing
- Use preemptible VMs (cheaper but can be terminated)

---

## 🔒 Production Recommendations

Before going live:

1. **Set up SSL/TLS** (wss:// instead of ws://)
   - Get SSL certificate (Let's Encrypt)
   - Update server code to use SSL
   - Update frontend to use wss://

2. **Use Domain Name**
   ```
   wss://trackd.yourdomain.com:8765
   ```

3. **Add Authentication** (if needed)
   - Token-based auth
   - API keys
   - Rate limiting

4. **Set up Monitoring**
   - Google Cloud Monitoring
   - Uptime checks
   - Alert on failures

5. **Enable Backups** (if saving results)

---

## 📖 Next Steps

### For You:
1. ✅ Follow `GCP_DEPLOYMENT_GUIDE.md`
2. ✅ Deploy to GCP VM
3. ✅ Configure firewall
4. ✅ Test server accessibility
5. ✅ Share server IP with frontend team

### For Frontend Team:
1. ✅ Read `FRONTEND_CLOUD_INTEGRATION.md`
2. ✅ Implement camera capture
3. ✅ Send frames to server
4. ✅ Handle results
5. ✅ Test end-to-end flow

---

## 🎉 Summary

**You now have:**
- ✅ Cloud-ready WebSocket server (`server_cloud.py`)
- ✅ Automated deployment script (`deploy.sh`)
- ✅ Production systemd service
- ✅ Complete deployment guide
- ✅ Frontend integration examples
- ✅ Monitoring and troubleshooting guides

**Total deployment time:** ~5-10 minutes

**Your server will:**
- ✅ Receive camera frames from browser
- ✅ Detect finger presence
- ✅ Analyze liveness (6 detection methods)
- ✅ Identify attack types
- ✅ Send results back in real-time
- ✅ Auto-restart after results
- ✅ Auto-start on VM boot
- ✅ Auto-restart on crash

---

## 🆘 Need Help?

**Documentation:**
- `GCP_DEPLOYMENT_GUIDE.md` - Deployment steps
- `FRONTEND_CLOUD_INTEGRATION.md` - Frontend integration
- `API_DOCUMENTATION.md` - API reference (original)

**Logs:**
```bash
sudo journalctl -u trackd -f
```

**Status:**
```bash
sudo systemctl status trackd
```

---

## 🚀 Ready to Deploy!

Start with:
```bash
# Read the guide first!
cat GCP_DEPLOYMENT_GUIDE.md

# Then follow the steps
# It's fully automated and takes ~5 minutes
```

**Good luck with your deployment!** 🎯
