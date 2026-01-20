# TRACK D - Frontend Cloud Integration Guide

## Camera Streaming from Browser to Cloud Server

This guide shows how to capture camera in the browser and stream frames to the cloud WebSocket server for processing.

---

## Architecture

```
Browser (Your Device) ──────────────► Cloud Server (GCP VM)
    │                                      │
    ├─ Capture camera (getUserMedia)       ├─ Receive frames
    ├─ Encode to JPEG                      ├─ Detect finger
    ├─ Convert to base64                   ├─ Analyze liveness
    └─ Send via WebSocket ───────────────► └─ Send results back
```

**Key Difference from Local Version:**
- **Local:** Server captures camera, streams video to frontend
- **Cloud:** Frontend captures camera, sends frames to server

---

## Quick Start

### 1. Connect to Server

```javascript
const ws = new WebSocket('ws://YOUR_GCP_VM_IP:8765');

ws.onopen = () => {
  console.log('Connected to TRACK D Cloud Server');

  // Start analysis session
  ws.send(JSON.stringify({ command: 'START_ANALYSIS' }));
};
```

### 2. Capture Browser Camera

```javascript
const video = document.getElementById('video');
const canvas = document.createElement('canvas');
const ctx = canvas.getContext('2d');

// Request camera access
navigator.mediaDevices.getUserMedia({
  video: {
    width: 800,
    height: 600,
    facingMode: 'user'  // Front camera
  }
})
.then(stream => {
  video.srcObject = stream;
  video.play();

  // Start sending frames
  startStreaming();
})
.catch(err => {
  console.error('Camera error:', err);
});
```

### 3. Send Frames to Server

```javascript
function startStreaming() {
  const FPS = 10;  // Send 10 frames per second

  setInterval(() => {
    // Draw current video frame to canvas
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // Convert to base64 JPEG
    const frameData = canvas.toDataURL('image/jpeg', 0.8);

    // Send to server
    ws.send(JSON.stringify({
      type: 'frame',
      frame: frameData
    }));
  }, 1000 / FPS);
}
```

### 4. Receive Results

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  console.log('Status:', data.status);
  console.log('Confidence:', data.confidence);
  console.log('Scores:', data.scores);

  if (data.result) {
    console.log('Result:', data.result);  // "LIVE" or "SPOOF"
    if (data.attack_type) {
      console.log('Attack detected:', data.attack_type);
    }
  }
};
```

---

## Complete Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>TRACK D - Cloud Liveness Detection</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }

    #video {
      width: 800px;
      height: 600px;
      border: 3px solid #333;
      display: block;
      margin: 20px auto;
    }

    .status {
      text-align: center;
      font-size: 32px;
      font-weight: bold;
      margin: 20px 0;
    }

    .status.waiting { color: gray; }
    .status.analyzing { color: blue; }
    .status.live { color: green; }
    .status.spoof { color: red; }

    .controls {
      text-align: center;
      margin: 20px 0;
    }

    button {
      font-size: 18px;
      padding: 15px 30px;
      margin: 0 10px;
      cursor: pointer;
      border-radius: 5px;
      border: none;
      background: #007bff;
      color: white;
    }

    button:hover {
      background: #0056b3;
    }

    .scores {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 15px;
      margin: 20px 0;
    }

    .score-item {
      background: #f0f0f0;
      padding: 15px;
      border-radius: 5px;
      text-align: center;
    }

    .score-value {
      font-size: 24px;
      font-weight: bold;
      color: #007bff;
    }

    .instruction {
      text-align: center;
      font-size: 18px;
      padding: 15px;
      background: #fff3cd;
      border-radius: 5px;
      margin: 20px 0;
    }

    .progress-bar {
      width: 100%;
      height: 30px;
      background: #e0e0e0;
      border-radius: 15px;
      overflow: hidden;
      margin: 20px 0;
    }

    .progress-fill {
      height: 100%;
      background: linear-gradient(90deg, #007bff, #0056b3);
      transition: width 0.3s ease;
    }
  </style>
</head>
<body>
  <h1 style="text-align: center;">TRACK D - Liveness Detection</h1>

  <!-- Video Element -->
  <video id="video" autoplay playsinline></video>

  <!-- Status -->
  <div id="status" class="status waiting">DISCONNECTED</div>

  <!-- Instruction -->
  <div id="instruction" class="instruction">Click "Start Verification" to begin</div>

  <!-- Progress Bar -->
  <div class="progress-bar">
    <div id="progress" class="progress-fill" style="width: 0%"></div>
  </div>

  <!-- Controls -->
  <div class="controls">
    <button id="startBtn">Start Verification</button>
    <button id="resetBtn">Reset</button>
    <button id="saveBtn">Save Result</button>
  </div>

  <!-- Scores -->
  <div class="scores">
    <div class="score-item">
      <div>Motion</div>
      <div id="score-motion" class="score-value">0%</div>
    </div>
    <div class="score-item">
      <div>Texture</div>
      <div id="score-texture" class="score-value">0%</div>
    </div>
    <div class="score-item">
      <div>Edge Density</div>
      <div id="score-edge" class="score-value">0%</div>
    </div>
    <div class="score-item">
      <div>Color Variance</div>
      <div id="score-color" class="score-value">0%</div>
    </div>
    <div class="score-item">
      <div>Consistency</div>
      <div id="score-consistency" class="score-value">0%</div>
    </div>
    <div class="score-item">
      <div>Overall</div>
      <div id="score-overall" class="score-value">0%</div>
    </div>
  </div>

  <script>
    // =====================================================
    // Configuration
    // =====================================================
    const SERVER_URL = 'ws://YOUR_GCP_VM_IP:8765';  // ← Change this!
    const FRAME_RATE = 10;  // Frames per second to send

    // =====================================================
    // Elements
    // =====================================================
    const video = document.getElementById('video');
    const statusEl = document.getElementById('status');
    const instructionEl = document.getElementById('instruction');
    const progressEl = document.getElementById('progress');

    const startBtn = document.getElementById('startBtn');
    const resetBtn = document.getElementById('resetBtn');
    const saveBtn = document.getElementById('saveBtn');

    // =====================================================
    // State
    // =====================================================
    let ws = null;
    let stream = null;
    let streamingInterval = null;
    let canvas = document.createElement('canvas');
    let ctx = canvas.getContext('2d');

    // =====================================================
    // WebSocket Connection
    // =====================================================
    function connect() {
      statusEl.textContent = 'CONNECTING...';
      statusEl.className = 'status waiting';

      ws = new WebSocket(SERVER_URL);

      ws.onopen = () => {
        console.log('Connected to server');
        statusEl.textContent = 'CONNECTED';
        instructionEl.textContent = 'Click "Start Verification" to begin';
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'connection') {
          console.log('Server ready:', data.message);
        } else if (data.type === 'status') {
          console.log('Status:', data.message);
        } else if (data.type === 'error') {
          alert('Error: ' + data.message);
        } else if (data.type === 'save_result') {
          alert('Result saved: ' + data.filename);
        } else {
          // Detection data
          updateUI(data);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        statusEl.textContent = 'CONNECTION ERROR';
        statusEl.className = 'status spoof';
      };

      ws.onclose = () => {
        console.log('Disconnected');
        statusEl.textContent = 'DISCONNECTED';
        statusEl.className = 'status waiting';
        stopStreaming();
      };
    }

    // =====================================================
    // Camera Access
    // =====================================================
    async function startCamera() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: 800,
            height: 600,
            facingMode: 'user'
          }
        });

        video.srcObject = stream;
        await video.play();

        console.log('Camera started');
      } catch (err) {
        console.error('Camera error:', err);
        alert('Could not access camera: ' + err.message);
      }
    }

    function stopCamera() {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
      }
    }

    // =====================================================
    // Frame Streaming
    // =====================================================
    function startStreaming() {
      if (streamingInterval) return;

      console.log('Starting frame streaming at', FRAME_RATE, 'FPS');

      streamingInterval = setInterval(() => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
          stopStreaming();
          return;
        }

        // Capture frame
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        ctx.drawImage(video, 0, 0);

        // Convert to base64 JPEG
        const frameData = canvas.toDataURL('image/jpeg', 0.8);

        // Send to server
        ws.send(JSON.stringify({
          type: 'frame',
          frame: frameData
        }));
      }, 1000 / FRAME_RATE);
    }

    function stopStreaming() {
      if (streamingInterval) {
        clearInterval(streamingInterval);
        streamingInterval = null;
        console.log('Stopped frame streaming');
      }
    }

    // =====================================================
    // UI Updates
    // =====================================================
    function updateUI(data) {
      // Status
      statusEl.textContent = data.status;
      statusEl.className = 'status ' + data.status.toLowerCase();

      // Instruction
      instructionEl.textContent = data.ui_elements.instruction;

      // Progress
      progressEl.style.width = data.ui_elements.progress + '%';

      // Scores
      document.getElementById('score-motion').textContent =
        data.scores.motion.toFixed(1) + '%';
      document.getElementById('score-texture').textContent =
        data.scores.texture.toFixed(1) + '%';
      document.getElementById('score-edge').textContent =
        data.scores.edge_density.toFixed(1) + '%';
      document.getElementById('score-color').textContent =
        data.scores.color_variance.toFixed(1) + '%';
      document.getElementById('score-consistency').textContent =
        data.scores.consistency.toFixed(1) + '%';
      document.getElementById('score-overall').textContent =
        data.scores.overall.toFixed(1) + '%';

      // Result
      if (data.result) {
        console.log('='.repeat(50));
        console.log('RESULT:', data.result);
        console.log('Confidence:', data.confidence.toFixed(2) + '%');
        if (data.attack_type) {
          console.log('Attack Type:', data.attack_type);
        }
        console.log('='.repeat(50));
      }
    }

    // =====================================================
    // Button Handlers
    // =====================================================
    startBtn.onclick = async () => {
      // Start camera if not started
      if (!stream) {
        await startCamera();
      }

      // Send START_ANALYSIS command
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: 'START_ANALYSIS' }));
        startStreaming();
      } else {
        alert('Not connected to server!');
      }
    };

    resetBtn.onclick = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: 'RESET' }));
      }
    };

    saveBtn.onclick = () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ command: 'SAVE_RESULT' }));
      }
    };

    // =====================================================
    // Initialize
    // =====================================================
    window.onload = () => {
      connect();
    };

    window.onbeforeunload = () => {
      stopStreaming();
      stopCamera();
      if (ws) ws.close();
    };
  </script>
</body>
</html>
```

---

## React Example

```jsx
import React, { useEffect, useState, useRef } from 'react';

function LivenessDetector() {
  const SERVER_URL = 'ws://YOUR_GCP_VM_IP:8765';  // ← Change this!
  const FRAME_RATE = 10;  // FPS

  const [ws, setWs] = useState(null);
  const [data, setData] = useState(null);
  const [status, setStatus] = useState('DISCONNECTED');

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);

  // Connect to WebSocket
  useEffect(() => {
    const websocket = new WebSocket(SERVER_URL);

    websocket.onopen = () => {
      console.log('Connected');
      setStatus('CONNECTED');
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (!message.type || message.type === 'data') {
        setData(message);
      } else if (message.type === 'error') {
        alert('Error: ' + message.message);
      }
    };

    websocket.onclose = () => {
      console.log('Disconnected');
      setStatus('DISCONNECTED');
    };

    setWs(websocket);

    return () => {
      websocket.close();
      stopStreaming();
      stopCamera();
    };
  }, []);

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 800, height: 600, facingMode: 'user' }
      });

      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      streamRef.current = stream;
    } catch (err) {
      alert('Camera error: ' + err.message);
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  };

  // Start streaming frames
  const startStreaming = () => {
    if (intervalRef.current) return;

    intervalRef.current = setInterval(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) return;

      const video = videoRef.current;
      const canvas = canvasRef.current;

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);

      const frameData = canvas.toDataURL('image/jpeg', 0.8);

      ws.send(JSON.stringify({
        type: 'frame',
        frame: frameData
      }));
    }, 1000 / FRAME_RATE);
  };

  // Stop streaming
  const stopStreaming = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  // Command handlers
  const handleStart = async () => {
    if (!streamRef.current) {
      await startCamera();
    }

    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ command: 'START_ANALYSIS' }));
      startStreaming();
    }
  };

  const handleReset = () => {
    ws?.send(JSON.stringify({ command: 'RESET' }));
  };

  const handleSave = () => {
    ws?.send(JSON.stringify({ command: 'SAVE_RESULT' }));
  };

  return (
    <div className="liveness-detector">
      <h1>TRACK D - Liveness Detection</h1>

      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Video Element */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        style={{ width: 800, height: 600, border: '3px solid #333' }}
      />

      {/* Status */}
      <div className={`status status-${data?.status?.toLowerCase() || status.toLowerCase()}`}>
        {data?.status || status}
      </div>

      {/* Instruction */}
      <div className="instruction">
        {data?.ui_elements?.instruction || 'Click Start to begin'}
      </div>

      {/* Progress Bar */}
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{ width: `${data?.ui_elements?.progress || 0}%` }}
        />
      </div>

      {/* Controls */}
      <div className="controls">
        <button onClick={handleStart}>Start Verification</button>
        <button onClick={handleReset}>Reset</button>
        <button onClick={handleSave}>Save Result</button>
      </div>

      {/* Scores */}
      <div className="scores">
        <div>Motion: {data?.scores?.motion?.toFixed(1) || 0}%</div>
        <div>Texture: {data?.scores?.texture?.toFixed(1) || 0}%</div>
        <div>Edge: {data?.scores?.edge_density?.toFixed(1) || 0}%</div>
        <div>Color: {data?.scores?.color_variance?.toFixed(1) || 0}%</div>
        <div>Consistency: {data?.scores?.consistency?.toFixed(1) || 0}%</div>
        <div>Overall: {data?.scores?.overall?.toFixed(1) || 0}%</div>
      </div>

      {/* Result */}
      {data?.result && (
        <div className={`result result-${data.result.toLowerCase()}`}>
          {data.result === 'LIVE' ? '✓ LIVE DETECTED' : '✗ SPOOF DETECTED'}
          {data.attack_type && <div>{data.attack_type}</div>}
        </div>
      )}
    </div>
  );
}

export default LivenessDetector;
```

---

## Important Notes

### Frame Rate Optimization

**Recommendation: 10 FPS**
- Good balance between responsiveness and bandwidth
- Server processes frames efficiently
- Reduces network usage

You can adjust based on your needs:
```javascript
const FRAME_RATE = 10;  // 10 FPS (recommended)
const FRAME_RATE = 15;  // 15 FPS (faster, more bandwidth)
const FRAME_RATE = 5;   // 5 FPS (slower, less bandwidth)
```

### Image Quality

```javascript
canvas.toDataURL('image/jpeg', 0.8);  // 80% quality (recommended)
canvas.toDataURL('image/jpeg', 0.6);  // 60% quality (smaller, faster)
canvas.toDataURL('image/jpeg', 1.0);  // 100% quality (larger, slower)
```

### Camera Resolution

```javascript
video: {
  width: 800,   // Standard (recommended)
  height: 600,
  facingMode: 'user'  // Front camera
}

// Or higher resolution
video: {
  width: 1280,  // HD
  height: 720,
  facingMode: 'user'
}
```

---

## Testing

1. **Update SERVER_URL** in the HTML/React code with your GCP VM IP
2. **Open** the HTML file in browser (or run React app)
3. **Allow** camera access when prompted
4. **Click** "Start Verification"
5. **Place** finger in front of camera
6. **Wait** for result (~5 seconds)
7. **Observe** auto-restart after 3 seconds

---

## Troubleshooting

### Camera Access Denied
- Check browser permissions
- Use HTTPS (required for camera access on non-localhost)
- Try different browser

### WebSocket Connection Failed
- Verify server is running
- Check firewall allows port 8765
- Verify VM IP address is correct
- Check browser console for errors

### Slow/Laggy
- Reduce FRAME_RATE (try 5 FPS)
- Reduce image quality (try 0.6)
- Reduce camera resolution (try 640x480)

### CORS Issues
- WebSocket doesn't have CORS restrictions
- Make sure you're using `ws://` not `http://`

---

## Production Considerations

### Use WSS (Secure WebSocket)

```javascript
const SERVER_URL = 'wss://your-domain.com:8765';  // Secure connection
```

Server needs SSL certificate.

### Add Reconnection Logic

```javascript
function connectWithRetry() {
  const ws = new WebSocket(SERVER_URL);

  ws.onclose = () => {
    console.log('Disconnected, retrying in 5s...');
    setTimeout(connectWithRetry, 5000);
  };

  return ws;
}
```

### Optimize Frame Sending

Only send frames when analysis is active:

```javascript
let analysisActive = false;

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'status' && data.analysis_active !== undefined) {
    analysisActive = data.analysis_active;
  }
};

// Only send if active
if (analysisActive && ws.readyState === WebSocket.OPEN) {
  ws.send(JSON.stringify({ type: 'frame', frame: frameData }));
}
```

---

## Summary

**Key Changes from Local Version:**

| Aspect | Local Version | Cloud Version |
|--------|--------------|---------------|
| Camera | Server captures | Frontend captures |
| Frame Flow | Server → Frontend | Frontend → Server |
| Data Sent | Video stream | Individual frames |
| Server Needs | Physical camera | No camera needed |

**Frontend Responsibilities:**
1. ✅ Capture browser camera
2. ✅ Encode frames to JPEG
3. ✅ Send frames to server
4. ✅ Receive and display results

**Server Responsibilities:**
1. ✅ Receive frames from frontend
2. ✅ Detect finger presence
3. ✅ Analyze liveness
4. ✅ Send results back

---

Ready to deploy! 🚀
