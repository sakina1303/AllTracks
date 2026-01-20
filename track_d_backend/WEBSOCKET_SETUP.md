# TRACK D - WebSocket Setup Guide

## Quick Start Guide for Local Testing

This guide will help you set up and test the WebSocket API locally.

---

## Prerequisites

- Python 3.8 or higher (you have Python 3.11.14 ✓)
- Webcam connected to your computer
- Terminal/Command Prompt access

---

## Installation Steps

### 1. Install Dependencies

```bash
# Navigate to TRACK_D directory
cd /home/user/TRACK_D

# Install all required packages
pip install -r requirements.txt
```

This will install:
- `opencv-python` - Computer vision
- `numpy` - Numerical operations
- `mediapipe` - Hand/finger detection
- `websockets` - WebSocket server/client

### 2. Verify Installation

```bash
# Check if packages are installed
pip list | grep -E "(opencv|numpy|mediapipe|websockets)"
```

You should see:
```
opencv-python              4.8.1.78
numpy                      1.24.3
mediapipe                  0.10.9
websockets                 12.0
```

---

## Running the Server

### Start the WebSocket Server

```bash
python server.py
```

Expected output:
```
======================================================================
        TRACK D: WebSocket Server
======================================================================

Validating configuration...
✓ Configuration validated successfully

Initializing components...
Initializing Liveness Detector...
✓ Liveness Detector ready!
Initializing Finger Detector...
Output directory: trackd_results/
✓ Server initialized!

======================================================================
Server starting on ws://localhost:8765
======================================================================

Configuration:
  FPS: 30
  Auto-restart after result: 3s
  Camera resolution: 800x600

Waiting for client connection...
======================================================================
```

**Server is now running!** Keep this terminal open.

---

## Testing with Python Client

### Open a New Terminal

```bash
# In a new terminal window
cd /home/user/TRACK_D

# Run the test client
python test_client.py
```

Expected output:
```
======================================================================
        TRACK D: Test Client
======================================================================

Server URL: ws://localhost:8765

Controls:
  S - Start Analysis
  R - Reset
  V - Save Result
  P - Pause streaming
  U - Resume streaming (Unpause)
  Q - Quit
======================================================================

[CONNECTING] ws://localhost:8765...
[CONNECTED] ✓

[SERVER] Connected to TRACK D server
  Available commands: ['START_ANALYSIS', 'RESET', 'SAVE_RESULT', 'STOP_STREAM', 'RESUME_STREAM']

[RECEIVING] Listening for messages...

[DISPLAY] Window opened
```

### Test Commands

1. **Press `S`** - Start Analysis
   - Camera should open
   - Video window appears
   - Server logs: `[START] Opening camera...`

2. **Place your finger in front of camera**
   - Status changes: WAITING → ANALYZING
   - Progress bar fills up
   - Scores update in real-time

3. **Wait for result** (~5 seconds)
   - Shows: LIVE ✓ or SPOOF ✗
   - Auto-restarts after 3 seconds

4. **Press `R`** - Reset analysis

5. **Press `V`** - Save result (only if LIVE)
   - Saves to `trackd_results/` folder

6. **Press `Q`** - Quit client

---

## Testing with Frontend

### For Your Frontend Team

1. **Share the API Documentation:**
   - File: `API_DOCUMENTATION.md`
   - Contains complete integration guide
   - JavaScript and React examples included

2. **Start the server:**
   ```bash
   python server.py
   ```

3. **Frontend connects to:**
   ```
   ws://localhost:8765
   ```

4. **Test the flow:**
   ```
   User clicks "Start Verification"
   → Frontend sends: {"command": "START_ANALYSIS"}
   → Server opens camera and streams
   → User places finger
   → Analysis runs (5 seconds)
   → Result appears: LIVE or SPOOF
   → Auto-restarts for next person
   ```

---

## File Overview

| File | Purpose |
|------|---------|
| `server.py` | WebSocket server (run this first) |
| `test_client.py` | Python test client (for local testing) |
| `API_DOCUMENTATION.md` | Complete API docs for frontend team |
| `WEBSOCKET_SETUP.md` | This setup guide |
| `requirements.txt` | Python dependencies |

---

## Important Features

### 1. Command-Controlled Flow

- Frontend has full control via commands
- User clicks "Start" → Camera opens
- Flexible and professional

### 2. Auto-Restart

- After showing result for 3 seconds
- Automatically resets for next person
- No manual intervention needed

### 3. Real-time Streaming

- 30 FPS video feed
- Live detection scores
- Progress updates

### 4. Comprehensive Data

Every message includes:
- Camera frame (base64 JPEG)
- Detection status
- All 6 detection scores
- Overall confidence
- Attack type (if detected)
- UI instructions
- Progress percentage

---

## Testing Checklist

- [ ] Server starts successfully
- [ ] Test client connects
- [ ] Camera opens when START_ANALYSIS sent
- [ ] Video feed displays
- [ ] Finger detection works
- [ ] Status changes: WAITING → ANALYZING → LIVE/SPOOF
- [ ] Scores update in real-time
- [ ] Progress bar fills to 100%
- [ ] Result displays correctly
- [ ] Auto-restart works (3 second delay)
- [ ] RESET command works
- [ ] SAVE_RESULT works (for LIVE results)
- [ ] Multiple test rounds work

---

## Expected Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. START: User opens frontend page                          │
│    - Frontend connects to ws://localhost:8765               │
│    - Shows "Start Verification" button                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. START ANALYSIS: User clicks button                       │
│    - Frontend sends: {"command": "START_ANALYSIS"}          │
│    - Server opens camera                                    │
│    - Server starts streaming at 30 FPS                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. WAITING: No finger detected                              │
│    - status: "WAITING"                                      │
│    - finger_detected: false                                 │
│    - instruction: "Show your finger to camera"              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. ANALYZING: Finger detected                               │
│    - status: "ANALYZING"                                    │
│    - finger_detected: true                                  │
│    - progress: 0% → 100%                                    │
│    - frames_analyzed: 0 → 15+                               │
│    - scores updating in real-time                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. RESULT: Analysis complete (~5 seconds)                   │
│    - status: "LIVE" or "SPOOF"                              │
│    - result: "LIVE" or "SPOOF"                              │
│    - confidence: 0-100%                                     │
│    - attack_type: if SPOOF                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. AUTO-RESTART: After 3 seconds                            │
│    - Server automatically resets                            │
│    - Back to WAITING state                                  │
│    - Ready for next person                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Troubleshooting

### Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'websockets'`

**Solution:**
```bash
pip install websockets
```

---

### Camera Error

**Error:** `Could not open camera`

**Solution:**
1. Close other apps using camera (Zoom, Skype, etc.)
2. Check camera permissions
3. Try different camera index:
   - Edit `server.py`, line 169
   - Change `cv2.VideoCapture(0)` to `cv2.VideoCapture(1)`

---

### Client Can't Connect

**Error:** `Connection refused`

**Solution:**
1. Ensure server is running first
2. Check server terminal for errors
3. Verify port 8765 is not blocked
4. Check firewall settings

---

### Low FPS

**Problem:** Video is laggy

**Solution:**
1. Reduce FPS in `server.py`:
   ```python
   FPS = 15  # Change from 30 to 15
   ```

2. Or adjust JPEG quality (line 447):
   ```python
   cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 70])  # Reduce from 85 to 70
   ```

---

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Start server: `python server.py`
3. ✅ Test with Python client: `python test_client.py`
4. ✅ Share `API_DOCUMENTATION.md` with frontend team
5. ✅ Frontend team builds UI using JavaScript/React examples
6. ✅ Test end-to-end integration

---

## Production Deployment

### For Production (Later):

1. **Change WebSocket URL:**
   ```python
   # In server.py
   WEBSOCKET_HOST = "0.0.0.0"  # Listen on all interfaces
   WEBSOCKET_PORT = 8765
   ```

2. **Use SSL/TLS (wss://):**
   - Get SSL certificate
   - Use `websockets.serve(..., ssl=ssl_context)`

3. **Add authentication:**
   - Token-based auth
   - Validate client connections

4. **Logging:**
   - Add proper logging (not just print)
   - Log to file for debugging

5. **Error handling:**
   - More robust error recovery
   - Reconnection logic

---

## Support

If you encounter issues:
1. Check this guide
2. Review `API_DOCUMENTATION.md`
3. Check server/client terminal output
4. Verify all dependencies installed

---

## Summary

You now have:
- ✅ WebSocket server (`server.py`)
- ✅ Test client (`test_client.py`)
- ✅ Complete API documentation (`API_DOCUMENTATION.md`)
- ✅ Setup guide (this file)
- ✅ Auto-restart functionality
- ✅ Command-controlled flow
- ✅ Real-time streaming at 30 FPS

**Ready for frontend integration!** 🚀
