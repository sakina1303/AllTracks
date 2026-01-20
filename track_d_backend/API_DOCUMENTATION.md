# TRACK D - WebSocket API Documentation

## Frontend Integration Guide

This document provides complete information for integrating the TRACK D liveness detection system into your frontend application.

---

## Table of Contents

1. [Overview](#overview)
2. [WebSocket Connection](#websocket-connection)
3. [Commands (Frontend → Server)](#commands-frontend--server)
4. [Messages (Server → Frontend)](#messages-server--frontend)
5. [Complete Flow](#complete-flow)
6. [JavaScript Examples](#javascript-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

**TRACK D** is a real-time liveness detection system that uses computer vision to distinguish real fingers from spoofing attempts (photos, screens, videos, fake fingers).

**Communication Protocol:** WebSocket (Binary + JSON)
**Default URL:** `ws://localhost:8765`
**Streaming FPS:** 30 FPS
**Auto-restart:** 3 seconds after result display

---

## WebSocket Connection

### Connection URL

```
ws://localhost:8765
```

For production, replace `localhost` with your server's IP/domain.

### Connection Flow

```
Client connects → Server sends welcome message → Client sends START_ANALYSIS →
Server starts streaming → Analysis runs → Result displayed → Auto-restart
```

---

## Commands (Frontend → Server)

Send commands as JSON objects:

```javascript
websocket.send(JSON.stringify({ command: "COMMAND_NAME" }));
```

### Available Commands

| Command | Description | When to Use |
|---------|-------------|-------------|
| `START_ANALYSIS` | Opens camera and begins streaming | User clicks "Start Verification" |
| `RESET` | Resets current analysis, starts fresh | User wants to try again |
| `SAVE_RESULT` | Saves current result (only if LIVE) | User wants to save verification |
| `STOP_STREAM` | Pauses streaming (keeps camera open) | Tab hidden / battery saving |
| `RESUME_STREAM` | Resumes streaming | Tab visible again |

### Command Examples

```javascript
// Start verification
websocket.send(JSON.stringify({ command: "START_ANALYSIS" }));

// Reset and try again
websocket.send(JSON.stringify({ command: "RESET" }));

// Save result
websocket.send(JSON.stringify({ command: "SAVE_RESULT" }));
```

---

## Messages (Server → Frontend)

The server sends two types of messages:

### 1. Status Messages

Sent in response to commands:

```json
{
  "type": "connection | status | error | save_result",
  "message": "Human-readable message",
  ...additional fields
}
```

#### Connection Message (on connect)

```json
{
  "type": "connection",
  "message": "Connected to TRACK D server",
  "status": "ready",
  "commands": ["START_ANALYSIS", "RESET", "SAVE_RESULT", "STOP_STREAM", "RESUME_STREAM"]
}
```

#### Status Message

```json
{
  "type": "status",
  "message": "Analysis started",
  "camera_resolution": [800, 600]
}
```

#### Error Message

```json
{
  "type": "error",
  "message": "Could not open camera"
}
```

#### Save Result Message

```json
{
  "type": "save_result",
  "message": "Result saved",
  "filename": "trackd_results/trackd_20260118_103045_0.png",
  "save_count": 1
}
```

### 2. Data Messages (Real-time Stream)

Sent continuously at 30 FPS during analysis:

```json
{
  "timestamp": "2026-01-18T10:30:45.123456",
  "frame": "base64_encoded_jpeg_image_data...",
  "frame_count": 45,
  "status": "ANALYZING",
  "finger_detected": true,
  "scores": {
    "motion": 85.5,
    "texture": 72.3,
    "edge_density": 68.1,
    "color_variance": 81.2,
    "pattern_detection": 65.4,
    "consistency": 75.0,
    "overall": 74.5
  },
  "result": null,
  "attack_type": null,
  "confidence": 74.5,
  "ui_elements": {
    "instruction": "Analyzing liveness...",
    "progress": 60.0
  },
  "frames_analyzed": 12
}
```

### Field Descriptions

| Field | Type | Description | Possible Values |
|-------|------|-------------|-----------------|
| `timestamp` | string | ISO format timestamp | e.g., "2026-01-18T10:30:45.123456" |
| `frame` | string | Base64 encoded JPEG image | Decode to display |
| `frame_count` | number | Total frames sent since start | 0, 1, 2, ... |
| `status` | string | Current detection status | `"WAITING"`, `"ANALYZING"`, `"LIVE"`, `"SPOOF"` |
| `finger_detected` | boolean | Whether finger is in frame | `true`, `false` |
| `scores` | object | All detection scores (0-100%) | See scores table below |
| `result` | string/null | Final result (when status is LIVE/SPOOF) | `null`, `"LIVE"`, `"SPOOF"` |
| `attack_type` | string/null | Type of attack detected | `null`, `"photo_attack"`, `"screen_attack"`, `"video_replay"`, `"fake_finger"` |
| `confidence` | number | Overall confidence (0-100%) | 0.0 to 100.0 |
| `ui_elements.instruction` | string | User instruction message | "Show your finger...", "Analyzing...", etc. |
| `ui_elements.progress` | number | Analysis progress (0-100%) | 0.0 to 100.0 |
| `frames_analyzed` | number | Frames analyzed so far | 0, 1, 2, ... |

### Detection Scores

All scores are percentages (0-100%):

| Score Name | What It Detects | Real Finger | Spoof |
|------------|-----------------|-------------|-------|
| `motion` | Natural hand tremor | 70-100% | 0-30% |
| `texture` | Skin texture complexity | 60-100% | 0-50% |
| `edge_density` | Surface edge patterns | 50-100% | 0-40% |
| `color_variance` | Color distribution | 60-100% | 0-50% |
| `pattern_detection` | Regular patterns (print/screen) | 60-100% | 0-40% |
| `consistency` | Temporal consistency | 70-100% | 0-50% |
| `overall` | Weighted combination | ≥70% = LIVE | <70% = SPOOF |

### Status States

| Status | Meaning | UI Suggestion |
|--------|---------|---------------|
| `WAITING` | No finger detected | Show "Place your finger in front of camera" |
| `ANALYZING` | Analyzing finger | Show progress bar, "Analyzing..." |
| `LIVE` | Real finger verified | Show success message, green checkmark |
| `SPOOF` | Attack detected | Show error message, red X, attack type |

### Attack Types

| Attack Type | Description | User Message |
|-------------|-------------|--------------|
| `photo_attack` | Printed photo/fingerprint | "Photo/Print detected - Use real finger" |
| `screen_attack` | Phone/tablet screen display | "Screen detected - Use real finger" |
| `video_replay` | Video replay attack | "Video replay detected - Use real finger" |
| `fake_finger` | Silicone/rubber replica | "Fake finger detected - Use real finger" |

---

## Complete Flow

### 1. User Opens Page

```
Frontend: Connect to WebSocket
Server: Send connection message
Frontend: Display "Start Verification" button
```

### 2. User Clicks "Start Verification"

```
Frontend: Send START_ANALYSIS command
Server: Open camera, send status message
Server: Begin streaming at 30 FPS
Frontend: Display camera feed
```

### 3. User Places Finger

```
Server: finger_detected = false, status = "WAITING"
Frontend: Show "Show your finger to camera"

User places finger in frame

Server: finger_detected = true, status = "ANALYZING"
Frontend: Show progress bar
```

### 4. Analysis Running

```
Server: Stream frames with increasing progress (0% → 100%)
Frontend: Update progress bar, display scores
Server: frames_analyzed increases (0 → 15+)
```

### 5. Result Reached

```
Server: status = "LIVE" or "SPOOF", result = "LIVE" or "SPOOF"
Frontend: Display result screen (green/red)

After 3 seconds (automatic):

Server: Auto-reset, status = "WAITING"
Frontend: Return to waiting state for next person
```

### 6. User Saves Result (Optional)

```
User clicks "Save" button (only if LIVE)
Frontend: Send SAVE_RESULT command
Server: Save image and metadata, send confirmation
Frontend: Show "Saved successfully"
```

---

## JavaScript Examples

### Complete Integration Example

```javascript
class LivenessDetector {
  constructor(wsUrl = 'ws://localhost:8765') {
    this.wsUrl = wsUrl;
    this.ws = null;
  }

  // Connect to server
  connect() {
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      console.log('Connected to TRACK D server');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Disconnected from server');
    };
  }

  // Handle incoming messages
  handleMessage(data) {
    // Status messages
    if (data.type) {
      if (data.type === 'connection') {
        console.log('Server ready:', data.message);
      } else if (data.type === 'error') {
        this.showError(data.message);
      } else if (data.type === 'save_result') {
        this.showSuccess('Result saved: ' + data.filename);
      }
      return;
    }

    // Data messages (streaming)
    this.updateUI(data);
  }

  // Update UI with detection data
  updateUI(data) {
    // Update video frame
    const imgElement = document.getElementById('video-frame');
    imgElement.src = 'data:image/jpeg;base64,' + data.frame;

    // Update status
    const statusElement = document.getElementById('status');
    statusElement.textContent = data.status;
    statusElement.className = 'status-' + data.status.toLowerCase();

    // Update progress
    const progressElement = document.getElementById('progress');
    progressElement.style.width = data.ui_elements.progress + '%';

    // Update instruction
    const instructionElement = document.getElementById('instruction');
    instructionElement.textContent = data.ui_elements.instruction;

    // Update confidence
    const confidenceElement = document.getElementById('confidence');
    confidenceElement.textContent = data.confidence.toFixed(1) + '%';

    // Update scores
    document.getElementById('score-motion').textContent = data.scores.motion.toFixed(1);
    document.getElementById('score-texture').textContent = data.scores.texture.toFixed(1);
    document.getElementById('score-overall').textContent = data.scores.overall.toFixed(1);

    // Show result
    if (data.result) {
      this.showResult(data.result, data.attack_type);
    }
  }

  // Show result (LIVE or SPOOF)
  showResult(result, attackType) {
    const resultElement = document.getElementById('result');

    if (result === 'LIVE') {
      resultElement.innerHTML = '✓ LIVE FINGER DETECTED';
      resultElement.className = 'result-live';
    } else {
      let message = '✗ SPOOF DETECTED';
      if (attackType) {
        message += '<br>' + attackType.replace('_', ' ').toUpperCase();
      }
      resultElement.innerHTML = message;
      resultElement.className = 'result-spoof';
    }
  }

  // Send commands
  startAnalysis() {
    this.ws.send(JSON.stringify({ command: 'START_ANALYSIS' }));
  }

  reset() {
    this.ws.send(JSON.stringify({ command: 'RESET' }));
  }

  saveResult() {
    this.ws.send(JSON.stringify({ command: 'SAVE_RESULT' }));
  }

  stopStream() {
    this.ws.send(JSON.stringify({ command: 'STOP_STREAM' }));
  }

  resumeStream() {
    this.ws.send(JSON.stringify({ command: 'RESUME_STREAM' }));
  }
}

// Usage
const detector = new LivenessDetector();
detector.connect();

// Button handlers
document.getElementById('start-btn').onclick = () => detector.startAnalysis();
document.getElementById('reset-btn').onclick = () => detector.reset();
document.getElementById('save-btn').onclick = () => detector.saveResult();
```

### HTML Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>TRACK D - Liveness Detection</title>
  <style>
    .status-waiting { color: gray; }
    .status-analyzing { color: blue; }
    .status-live { color: green; }
    .status-spoof { color: red; }

    .result-live {
      background: green;
      color: white;
      padding: 20px;
      font-size: 24px;
    }

    .result-spoof {
      background: red;
      color: white;
      padding: 20px;
      font-size: 24px;
    }

    #video-frame {
      width: 800px;
      height: 600px;
      border: 2px solid #333;
    }

    .progress-bar {
      width: 100%;
      height: 30px;
      background: #ddd;
    }

    .progress-fill {
      height: 100%;
      background: blue;
      transition: width 0.3s;
    }
  </style>
</head>
<body>
  <h1>TRACK D - Liveness Detection</h1>

  <!-- Video Display -->
  <img id="video-frame" src="" alt="Camera Feed">

  <!-- Status -->
  <div>
    <h2>Status: <span id="status">Disconnected</span></h2>
    <h3 id="instruction">Click Start to begin</h3>
  </div>

  <!-- Progress Bar -->
  <div class="progress-bar">
    <div id="progress" class="progress-fill" style="width: 0%"></div>
  </div>

  <!-- Confidence -->
  <div>
    <h3>Confidence: <span id="confidence">0%</span></h3>
  </div>

  <!-- Scores -->
  <div>
    <h3>Scores:</h3>
    <p>Motion: <span id="score-motion">0</span>%</p>
    <p>Texture: <span id="score-texture">0</span>%</p>
    <p>Overall: <span id="score-overall">0</span>%</p>
  </div>

  <!-- Result -->
  <div id="result"></div>

  <!-- Controls -->
  <button id="start-btn">Start Verification</button>
  <button id="reset-btn">Reset</button>
  <button id="save-btn">Save Result</button>

  <script src="liveness-detector.js"></script>
</body>
</html>
```

### React Example

```jsx
import React, { useEffect, useState, useRef } from 'react';

function LivenessDetector() {
  const [ws, setWs] = useState(null);
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  const imgRef = useRef(null);

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8765');

    websocket.onopen = () => {
      console.log('Connected');
      setConnected(true);
    };

    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);

      if (!message.type) {
        // Data message
        setData(message);

        // Update image
        if (imgRef.current && message.frame) {
          imgRef.current.src = 'data:image/jpeg;base64,' + message.frame;
        }
      }
    };

    websocket.onclose = () => {
      console.log('Disconnected');
      setConnected(false);
    };

    setWs(websocket);

    return () => websocket.close();
  }, []);

  const sendCommand = (command) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ command }));
    }
  };

  return (
    <div className="liveness-detector">
      <h1>TRACK D - Liveness Detection</h1>

      {/* Video Feed */}
      <img
        ref={imgRef}
        alt="Camera Feed"
        style={{ width: 800, height: 600, border: '2px solid #333' }}
      />

      {/* Status */}
      <div className={`status status-${data?.status?.toLowerCase()}`}>
        Status: {data?.status || 'Disconnected'}
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

      {/* Confidence */}
      <div>
        Confidence: {data?.confidence?.toFixed(1) || 0}%
      </div>

      {/* Scores */}
      <div className="scores">
        <h3>Scores:</h3>
        <p>Motion: {data?.scores?.motion?.toFixed(1) || 0}%</p>
        <p>Texture: {data?.scores?.texture?.toFixed(1) || 0}%</p>
        <p>Overall: {data?.scores?.overall?.toFixed(1) || 0}%</p>
      </div>

      {/* Result */}
      {data?.result && (
        <div className={`result result-${data.result.toLowerCase()}`}>
          {data.result === 'LIVE' ? '✓ LIVE FINGER DETECTED' : '✗ SPOOF DETECTED'}
          {data.attack_type && <div>{data.attack_type.replace('_', ' ').toUpperCase()}</div>}
        </div>
      )}

      {/* Controls */}
      <div className="controls">
        <button onClick={() => sendCommand('START_ANALYSIS')} disabled={!connected}>
          Start Verification
        </button>
        <button onClick={() => sendCommand('RESET')}>
          Reset
        </button>
        <button onClick={() => sendCommand('SAVE_RESULT')}>
          Save Result
        </button>
      </div>
    </div>
  );
}

export default LivenessDetector;
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Problem:** Cannot connect to WebSocket
**Solution:**
- Ensure server is running: `python server.py`
- Check firewall settings
- Verify correct URL and port

#### 2. No Video Displayed

**Problem:** Frames not showing
**Solution:**
- Check base64 decoding
- Verify image element src is updated
- Check browser console for errors

#### 3. Camera Not Opening

**Problem:** Server reports camera error
**Solution:**
- Check camera permissions
- Close other apps using camera
- Verify camera is connected

#### 4. Low Performance

**Problem:** Laggy video feed
**Solution:**
- Reduce FPS in server.py (change `FPS = 30` to `FPS = 15`)
- Check network connection
- Optimize frame display (use requestAnimationFrame)

#### 5. Server Busy Error

**Problem:** "Server busy - another client is connected"
**Solution:**
- Only one client can connect at a time
- Close other client connections
- Wait for previous client to disconnect

---

## Testing

### Local Testing Steps

1. **Start the server:**
   ```bash
   python server.py
   ```

2. **Run the test client:**
   ```bash
   python test_client.py
   ```

3. **Test commands:**
   - Press `S` to start analysis
   - Press `R` to reset
   - Press `V` to save result
   - Press `Q` to quit

### Expected Behavior

1. **WAITING State:** Shows "Show your finger to camera"
2. **Finger Detected:** Status changes to "ANALYZING"
3. **Analysis Progress:** Progress bar fills 0% → 100%
4. **Result:** After ~5 seconds, shows "LIVE" or "SPOOF"
5. **Auto-restart:** After 3 seconds, resets automatically

---

## Support

For questions or issues:
- GitHub: [Your Repo URL]
- Email: [Your Email]
- Documentation: This file

---

## Version

- API Version: 1.0
- Server: Python 3.8+
- WebSocket Protocol: RFC 6455
- Created: 2026-01-18
