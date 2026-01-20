# Track D - Liveness/Spoof Detection Setup

## ✅ Implementation Complete

Track D has been successfully implemented with **Liveness/Spoof Detection** using motion-based cues, texture analysis, and multi-frame consistency checks.

---

## 🎯 Features Implemented

### Frontend (React Native/Expo)
- **Multi-frame camera capture** (3 frames minimum)
- **Front-facing camera** for selfie liveness detection
- **Real-time frame counter** showing progress (0/3, 1/3, 2/3)
- **Visual feedback** with success/failure indicators
- **Score display** for motion, texture, and consistency
- **User-friendly UI** with clear instructions

### Backend (FastAPI + OpenCV)
- **Motion Detection**: Optical flow analysis between consecutive frames
- **Texture Analysis**: Laplacian variance to detect blur/print attacks
- **Consistency Check**: Histogram correlation across frames
- **Real-time processing**: Multi-frame liveness verification
- **Threshold-based decisions**: Configurable spoof detection thresholds

---

## 📂 File Structure

```
deployment/
├── finger_match_frontend/
│   └── screens/
│       └── TrackDScreen.js         ✅ Liveness detection UI
├── track_d_backend/
│   ├── api_track_d.py              ✅ Liveness detection algorithms
│   ├── requirements.txt
│   └── README.md
└── venv/                           ✅ Python virtual environment
```

---

## 🚀 Backend Status

### Track C (Fingerprint Matching)
- **Port**: 8000
- **URL**: http://192.168.139.152:8000
- **Status**: ✅ Running (DEMO mode - model needs fix)
- **Health**: `curl http://192.168.139.152:8000/health`

### Track D (Liveness Detection)
- **Port**: 8001
- **URL**: http://192.168.139.152:8001
- **Status**: ✅ Running
- **Health**: `curl http://192.168.139.152:8001/health`

---

## 🔬 Liveness Detection Algorithm

### 1. Motion Score (Optical Flow)
```python
# Detects micro-movements between frames
# Live faces: motion > 0.15
# Spoofs (photos/screens): motion < 0.15
```

### 2. Texture Score (Laplacian Variance)
```python
# Analyzes image sharpness and detail
# Live faces: texture > 0.3 (high detail)
# Spoofs: texture < 0.3 (blurry, low detail)
```

### 3. Consistency Score (Histogram Correlation)
```python
# Checks frame-to-frame consistency
# Live faces: consistency > 0.6
# Spoofs: consistency may vary due to screen refresh
```

### Decision Logic
```python
is_live = (motion > 0.15) AND (texture > 0.3) AND (consistency > 0.6)
confidence = (motion * 0.4) + (texture * 0.3) + (consistency * 0.3)
```

---

## 🧪 Testing Track D

### 1. Start the Backend (if not running)
```bash
cd /Users/sakina/Downloads/deployment
source venv/bin/activate
nohup python track_d_backend/api_track_d.py > track_d_backend.log 2>&1 &
```

### 2. Verify Backend Health
```bash
curl http://192.168.139.152:8001/health
# Should return: {"status":"healthy","service":"Track D - Liveness Detection"}
```

### 3. Test from Mobile App
1. Open the app on your device/emulator
2. Navigate to **Track D - Liveness Detection**
3. Tap **Start Liveness Check**
4. Camera will open (front-facing)
5. Tap **Capture Frame** 3 times (or as many as needed)
6. Tap **Process Liveness**
7. View results: ✅ LIVE or ⚠️ SPOOF DETECTED

---

## 📊 Expected Results

### Live Face (Real Person)
```json
{
  "is_live": true,
  "confidence": 0.78,
  "motion_score": 0.45,
  "texture_score": 0.82,
  "consistency_score": 0.91,
  "message": "LIVE"
}
```

### Spoof Attack (Photo/Screen)
```json
{
  "is_live": false,
  "confidence": 0.32,
  "motion_score": 0.08,
  "texture_score": 0.25,
  "consistency_score": 0.55,
  "message": "SPOOF DETECTED"
}
```

---

## 🔧 Customization

### Adjust Detection Thresholds
Edit `track_d_backend/api_track_d.py`:

```python
# Line ~140 - Modify thresholds
is_live = (
    motion_score > 0.15 and      # More motion = harder to spoof
    texture_score > 0.3 and      # More texture = harder to fake
    consistency_score > 0.6      # More consistency = natural
)
```

### Change Frame Requirements
Edit `finger_match_frontend/screens/TrackDScreen.js`:

```javascript
// Line ~20 - Modify minimum frames
const MIN_FRAMES = 3;  // Change to 4, 5, etc.
```

---

## 📱 API Endpoints

### Health Check
```bash
GET http://192.168.139.152:8001/health
```

### Liveness Detection
```bash
POST http://192.168.139.152:8001/api/liveness_check
Content-Type: multipart/form-data

Body:
- frames[0]: (binary image data)
- frames[1]: (binary image data)
- frames[2]: (binary image data)
```

---

## 🐛 Troubleshooting

### Backend Not Responding
```bash
# Check if running
ps aux | grep api_track_d

# Restart backend
cd /Users/sakina/Downloads/deployment
source venv/bin/activate
python track_d_backend/api_track_d.py
```

### Frontend Can't Connect
1. Verify your device is on the same Wi-Fi as the Mac
2. Check LAN IP hasn't changed:
   ```bash
   ipconfig getifaddr en0
   ```
3. Update `TrackDScreen.js` if IP changed:
   ```javascript
   const BACKEND_URL = 'http://NEW_IP_HERE:8001';
   ```

### Camera Not Working
- Ensure camera permissions are granted in the app
- Check expo-camera is properly installed
- Try restarting the Expo app

---

## ✨ Next Steps

1. **Test on physical device** (emulator camera may not work well)
2. **Collect real spoof samples** (photos, videos, masks)
3. **Tune thresholds** based on real-world testing
4. **Add face detection** (optional: detect face before liveness check)
5. **Improve UX** (add progress indicators, better instructions)

---

## 📝 Notes

- **Track C** is running in DEMO mode because `track_c_final.h5` is corrupted
- Backend team needs to re-export the model with TensorFlow 2.13.x
- Both backends use the same virtual environment (`venv/`)
- CORS is enabled for mobile access on both backends

---

**Status**: ✅ Track D is fully functional and ready for testing!
# Track D - Liveness/Spoof Detection Setup

## ✅ Implementation Complete

Track D has been successfully implemented with **Liveness/Spoof Detection** using motion-based cues, texture analysis, and multi-frame consistency checks.

---

## 🎯 Features Implemented

### Frontend (React Native/Expo)
- **Multi-frame camera capture** (3 frames minimum)
- **Front-facing camera** for selfie liveness detection
- **Real-time frame counter** showing progress (0/3, 1/3, 2/3)
- **Visual feedback** with success/failure indicators
- **Score display** for motion, texture, and consistency
- **User-friendly UI** with clear instructions

### Backend (FastAPI + OpenCV)
- **Motion Detection**: Optical flow analysis between consecutive frames
- **Texture Analysis**: Laplacian variance to detect blur/print attacks
- **Consistency Check**: Histogram correlation across frames
- **Real-time processing**: Multi-frame liveness verification
- **Threshold-based decisions**: Configurable spoof detection thresholds

---

## 📂 File Structure

```
deployment/
├── finger_match_frontend/
│   └── screens/
│       └── TrackDScreen.js         ✅ Liveness detection UI
├── track_d_backend/
│   ├── api_track_d.py              ✅ Liveness detection algorithms
│   ├── requirements.txt
│   └── README.md
└── venv/                           ✅ Python virtual environment
```

---

## 🚀 Backend Status

### Track C (Fingerprint Matching)
- **Port**: 8000
- **URL**: http://192.168.139.152:8000
- **Status**: ✅ Running (DEMO mode - model needs fix)
- **Health**: `curl http://192.168.139.152:8000/health`

### Track D (Liveness Detection)
- **Port**: 8001
- **URL**: http://192.168.139.152:8001
- **Status**: ✅ Running
- **Health**: `curl http://192.168.139.152:8001/health`

---

## 🔬 Liveness Detection Algorithm

### 1. Motion Score (Optical Flow)
```python
# Detects micro-movements between frames
# Live faces: motion > 0.15
# Spoofs (photos/screens): motion < 0.15
```

### 2. Texture Score (Laplacian Variance)
```python
# Analyzes image sharpness and detail
# Live faces: texture > 0.3 (high detail)
# Spoofs: texture < 0.3 (blurry, low detail)
```

### 3. Consistency Score (Histogram Correlation)
```python
# Checks frame-to-frame consistency
# Live faces: consistency > 0.6
# Spoofs: consistency may vary due to screen refresh
```

### Decision Logic
```python
is_live = (motion > 0.15) AND (texture > 0.3) AND (consistency > 0.6)
confidence = (motion * 0.4) + (texture * 0.3) + (consistency * 0.3)
```

---

## 🧪 Testing Track D

### 1. Start the Backend (if not running)
```bash
cd /Users/sakina/Downloads/deployment
source venv/bin/activate
nohup python track_d_backend/api_track_d.py > track_d_backend.log 2>&1 &
```

### 2. Verify Backend Health
```bash
curl http://192.168.139.152:8001/health
# Should return: {"status":"healthy","service":"Track D - Liveness Detection"}
```

### 3. Test from Mobile App
1. Open the app on your device/emulator
2. Navigate to **Track D - Liveness Detection**
3. Tap **Start Liveness Check**
4. Camera will open (front-facing)
5. Tap **Capture Frame** 3 times (or as many as needed)
6. Tap **Process Liveness**
7. View results: ✅ LIVE or ⚠️ SPOOF DETECTED

---

## 📊 Expected Results

### Live Face (Real Person)
```json
{
  "is_live": true,
  "confidence": 0.78,
  "motion_score": 0.45,
  "texture_score": 0.82,
  "consistency_score": 0.91,
  "message": "LIVE"
}
```

### Spoof Attack (Photo/Screen)
```json
{
  "is_live": false,
  "confidence": 0.32,
  "motion_score": 0.08,
  "texture_score": 0.25,
  "consistency_score": 0.55,
  "message": "SPOOF DETECTED"
}
```

---

## 🔧 Customization

### Adjust Detection Thresholds
Edit `track_d_backend/api_track_d.py`:

```python
# Line ~140 - Modify thresholds
is_live = (
    motion_score > 0.15 and      # More motion = harder to spoof
    texture_score > 0.3 and      # More texture = harder to fake
    consistency_score > 0.6      # More consistency = natural
)
```

### Change Frame Requirements
Edit `finger_match_frontend/screens/TrackDScreen.js`:

```javascript
// Line ~20 - Modify minimum frames
const MIN_FRAMES = 3;  // Change to 4, 5, etc.
```

---

## 📱 API Endpoints

### Health Check
```bash
GET http://192.168.139.152:8001/health
```

### Liveness Detection
```bash
POST http://192.168.139.152:8001/api/liveness_check
Content-Type: multipart/form-data

Body:
- frames[0]: (binary image data)
- frames[1]: (binary image data)
- frames[2]: (binary image data)
```

---

## 🐛 Troubleshooting

### Backend Not Responding
```bash
# Check if running
ps aux | grep api_track_d

# Restart backend
cd /Users/sakina/Downloads/deployment
source venv/bin/activate
python track_d_backend/api_track_d.py
```

### Frontend Can't Connect
1. Verify your device is on the same Wi-Fi as the Mac
2. Check LAN IP hasn't changed:
   ```bash
   ipconfig getifaddr en0
   ```
3. Update `TrackDScreen.js` if IP changed:
   ```javascript
   const BACKEND_URL = 'http://NEW_IP_HERE:8001';
   ```

### Camera Not Working
- Ensure camera permissions are granted in the app
- Check expo-camera is properly installed
- Try restarting the Expo app

---

## ✨ Next Steps

1. **Test on physical device** (emulator camera may not work well)
2. **Collect real spoof samples** (photos, videos, masks)
3. **Tune thresholds** based on real-world testing
4. **Add face detection** (optional: detect face before liveness check)
5. **Improve UX** (add progress indicators, better instructions)

---

## 📝 Notes

- **Track C** is running in DEMO mode because `track_c_final.h5` is corrupted
- Backend team needs to re-export the model with TensorFlow 2.13.x
- Both backends use the same virtual environment (`venv/`)
- CORS is enabled for mobile access on both backends

---

**Status**: ✅ Track D is fully functional and ready for testing!
