"""
TRACK D - WebSocket Server
Real-time Liveness Detection API for Frontend Integration

This server provides WebSocket streaming of camera feed with real-time
liveness detection analysis.

WebSocket URL: ws://localhost:8765

Commands (from frontend → server):
- START_ANALYSIS: Begin camera and analysis
- RESET: Clear current analysis and restart
- SAVE_RESULT: Save current result (if LIVE)
- STOP_STREAM: Pause streaming
- RESUME_STREAM: Resume streaming

Message format (server → frontend):
{
    "timestamp": "ISO format timestamp",
    "frame": "base64 encoded JPEG image",
    "status": "WAITING|ANALYZING|LIVE|SPOOF",
    "finger_detected": true/false,
    "scores": {
        "motion": 0.0-1.0,
        "texture": 0.0-1.0,
        "edge_density": 0.0-1.0,
        "color_variance": 0.0-1.0,
        "pattern_detection": 0.0-1.0,
        "consistency": 0.0-1.0,
        "overall": 0.0-100.0
    },
    "result": null | "LIVE" | "SPOOF",
    "attack_type": null | "photo_attack" | "screen_attack" | "video_replay" | "fake_finger",
    "confidence": 0.0-100.0,
    "ui_elements": {
        "instruction": "message for user",
        "progress": 0-100
    },
    "frames_analyzed": 0
}
"""

import asyncio
import websockets
import json
import cv2
import numpy as np
import base64
from datetime import datetime
import os
import traceback

# Import Track D components
import config
from liveness_detector import LivenessDetector
from finger_detector import FingerDetector

# Server configuration
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765
FPS = 30  # Target FPS for streaming
RESULT_DISPLAY_TIME = 3  # Seconds to show result before auto-restart


class LivenessWebSocketServer:
    """WebSocket server for liveness detection streaming."""

    def __init__(self):
        """Initialize server."""
        print("="*70)
        print("        TRACK D: WebSocket Server")
        print("="*70)

        # Validate configuration
        print("\nValidating configuration...")
        config.validate_config()

        # Initialize components
        print("\nInitializing components...")
        self.liveness_detector = LivenessDetector()
        self.finger_detector = FingerDetector()

        # Create output directory
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        print(f"Output directory: {config.OUTPUT_DIR}/")

        # Server state
        self.camera = None
        self.is_streaming = False
        self.analysis_active = False
        self.current_client = None
        self.saved_count = 0

        # Result timing
        self.result_timestamp = None
        self.auto_restart_enabled = True

        print("✓ Server initialized!")

    async def handle_client(self, websocket, path):
        """
        Handle WebSocket client connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_address = websocket.remote_address
        print(f"\n[CONNECTED] Client: {client_address}")

        # Only allow one client at a time
        if self.current_client is not None:
            await websocket.send(json.dumps({
                "error": "Server busy - another client is connected"
            }))
            await websocket.close()
            print(f"[REJECTED] Client {client_address} - server busy")
            return

        self.current_client = websocket

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection",
                "message": "Connected to TRACK D server",
                "status": "ready",
                "commands": ["START_ANALYSIS", "RESET", "SAVE_RESULT", "STOP_STREAM", "RESUME_STREAM"]
            }))

            # Listen for commands
            async for message in websocket:
                try:
                    data = json.loads(message)
                    command = data.get("command", "").upper()

                    print(f"[COMMAND] Received: {command}")

                    if command == "START_ANALYSIS":
                        await self.start_analysis(websocket)

                    elif command == "RESET":
                        await self.reset_analysis(websocket)

                    elif command == "SAVE_RESULT":
                        await self.save_result(websocket)

                    elif command == "STOP_STREAM":
                        self.is_streaming = False
                        await websocket.send(json.dumps({
                            "type": "status",
                            "message": "Streaming paused"
                        }))

                    elif command == "RESUME_STREAM":
                        if self.analysis_active:
                            self.is_streaming = True
                            await websocket.send(json.dumps({
                                "type": "status",
                                "message": "Streaming resumed"
                            }))

                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": f"Unknown command: {command}"
                        }))

                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                except Exception as e:
                    print(f"[ERROR] Command handling: {e}")
                    traceback.print_exc()

        except websockets.exceptions.ConnectionClosed:
            print(f"[DISCONNECTED] Client: {client_address}")

        finally:
            # Cleanup
            self.current_client = None
            if self.analysis_active:
                await self.stop_analysis()
            print(f"[CLEANUP] Client {client_address} disconnected")

    async def start_analysis(self, websocket):
        """
        Start camera and analysis.

        Args:
            websocket: WebSocket connection
        """
        if self.analysis_active:
            await websocket.send(json.dumps({
                "type": "status",
                "message": "Analysis already active"
            }))
            return

        print("\n[START] Opening camera and starting analysis...")

        # Open camera
        self.camera = cv2.VideoCapture(0)

        if not self.camera.isOpened():
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Could not open camera"
            }))
            print("[ERROR] Could not open camera!")
            return

        # Set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.WINDOW_WIDTH)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WINDOW_HEIGHT)

        # Reset detector
        self.liveness_detector.reset()

        # Start streaming
        self.analysis_active = True
        self.is_streaming = True

        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis started",
            "camera_resolution": [config.WINDOW_WIDTH, config.WINDOW_HEIGHT]
        }))

        print("✓ Camera opened, streaming started")

        # Start streaming loop
        await self.stream_loop(websocket)

    async def stop_analysis(self):
        """Stop camera and analysis."""
        print("\n[STOP] Stopping analysis...")

        self.analysis_active = False
        self.is_streaming = False

        if self.camera is not None:
            self.camera.release()
            self.camera = None

        print("✓ Camera released")

    async def reset_analysis(self, websocket):
        """
        Reset analysis to start fresh.

        Args:
            websocket: WebSocket connection
        """
        print("\n[RESET] Resetting analysis...")

        self.liveness_detector.reset()
        self.result_timestamp = None

        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis reset"
        }))

        print("✓ Analysis reset")

    async def save_result(self, websocket):
        """
        Save current result.

        Args:
            websocket: WebSocket connection
        """
        if not self.liveness_detector.is_live:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Cannot save - not LIVE"
            }))
            return

        # Capture current frame
        if self.camera is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "No camera active"
            }))
            return

        ret, frame = self.camera.read()
        if not ret:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Failed to capture frame"
            }))
            return

        # Save to disk
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.OUTPUT_DIR}/trackd_{timestamp}_{self.saved_count}.png"

            cv2.imwrite(filename, frame)

            self.saved_count += 1

            await websocket.send(json.dumps({
                "type": "save_result",
                "message": "Result saved",
                "filename": filename,
                "save_count": self.saved_count
            }))

            print(f"✓ Result saved: {filename}")

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Save failed: {str(e)}"
            }))
            print(f"[ERROR] Save failed: {e}")

    async def stream_loop(self, websocket):
        """
        Main streaming loop.

        Args:
            websocket: WebSocket connection
        """
        frame_interval = 1.0 / FPS
        frame_count = 0

        print(f"\n[STREAMING] Starting at {FPS} FPS...")

        while self.analysis_active:
            try:
                if not self.is_streaming:
                    await asyncio.sleep(0.1)
                    continue

                loop_start = asyncio.get_event_loop().time()

                # Read frame
                ret, frame = self.camera.read()

                if not ret:
                    print("[WARNING] Failed to read frame")
                    await asyncio.sleep(0.1)
                    continue

                frame_count += 1

                # Detect finger
                finger_detected = self.finger_detector.is_finger_visible(frame)

                # Analyze frame
                result = self.liveness_detector.analyze_frame(frame, finger_detected)

                # Check for auto-restart
                if self.auto_restart_enabled and result['status'] in ['LIVE', 'SPOOF']:
                    # Mark timestamp when result first appears
                    if self.result_timestamp is None:
                        self.result_timestamp = datetime.now()
                        print(f"\n[RESULT] {result['status']} - Auto-restart in {RESULT_DISPLAY_TIME}s")
                    else:
                        # Check if display time elapsed
                        elapsed = (datetime.now() - self.result_timestamp).total_seconds()
                        if elapsed >= RESULT_DISPLAY_TIME:
                            print("\n[AUTO-RESTART] Resetting for next person...")
                            self.liveness_detector.reset()
                            self.result_timestamp = None

                # Encode frame to JPEG
                _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Create message
                message = self.create_message(result, frame_base64, finger_detected, frame_count)

                # Send to client
                await websocket.send(json.dumps(message))

                # Maintain FPS
                elapsed = asyncio.get_event_loop().time() - loop_start
                sleep_time = max(0, frame_interval - elapsed)
                await asyncio.sleep(sleep_time)

            except websockets.exceptions.ConnectionClosed:
                print("[INFO] Connection closed during streaming")
                break

            except Exception as e:
                print(f"[ERROR] Stream loop: {e}")
                traceback.print_exc()
                await asyncio.sleep(0.1)

        print(f"\n[STREAMING] Stopped. Total frames: {frame_count}")

    def create_message(self, result, frame_base64, finger_detected, frame_count):
        """
        Create WebSocket message with all detection data.

        Args:
            result: Analysis result from liveness detector
            frame_base64: Base64 encoded frame
            finger_detected: Whether finger is detected
            frame_count: Current frame number

        Returns:
            dict: Complete message
        """
        # Convert scores to percentages
        scores_percentage = {
            key: round(value * 100, 2) for key, value in result['scores'].items()
        }
        scores_percentage['overall'] = round(result['overall_score'] * 100, 2)

        message = {
            "timestamp": datetime.now().isoformat(),
            "frame": frame_base64,
            "frame_count": frame_count,
            "status": result['status'],
            "finger_detected": finger_detected,
            "scores": scores_percentage,
            "result": result['status'] if result['status'] in ['LIVE', 'SPOOF'] else None,
            "attack_type": result['attack_type'],
            "confidence": round(result['confidence'] * 100, 2),
            "ui_elements": {
                "instruction": result['instruction'],
                "progress": round(result['progress'], 1)
            },
            "frames_analyzed": result['frames_analyzed']
        }

        return message


async def main():
    """Main server entry point."""
    server = LivenessWebSocketServer()

    print(f"\n{'='*70}")
    print(f"Server starting on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    print(f"{'='*70}\n")

    print("Configuration:")
    print(f"  FPS: {FPS}")
    print(f"  Auto-restart after result: {RESULT_DISPLAY_TIME}s")
    print(f"  Camera resolution: {config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
    print(f"\nWaiting for client connection...")
    print(f"{'='*70}\n")

    async with websockets.serve(server.handle_client, WEBSOCKET_HOST, WEBSOCKET_PORT):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[SHUTDOWN] Server stopped by user")
    except Exception as e:
        print(f"\n\n[ERROR] Server crashed: {e}")
        traceback.print_exc()
