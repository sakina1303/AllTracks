"""
TRACK D - Cloud WebSocket Server (Frontend Camera Version)
Real-time Liveness Detection API for Frontend Integration

This server receives camera frames FROM the frontend (browser camera),
processes them, and sends back detection results.

WebSocket URL: ws://YOUR_VM_IP:8765

Commands (from frontend → server):
- START_ANALYSIS: Begin analysis session
- RESET: Clear current analysis and restart
- SAVE_RESULT: Save current result (if LIVE)
- STOP_ANALYSIS: Stop current session

Data Messages (from frontend → server):
{
    "type": "frame",
    "frame": "base64_encoded_jpeg_image"
}

Response Messages (server → frontend):
{
    "timestamp": "ISO format timestamp",
    "status": "WAITING|ANALYZING|LIVE|SPOOF",
    "finger_detected": true/false,
    "scores": {...},
    "result": null | "LIVE" | "SPOOF",
    "attack_type": null | "photo_attack" | "screen_attack" | ...,
    "confidence": 0.0-100.0,
    "ui_elements": {...},
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
import logging

# Import Track D components
import config
from liveness_detector import LivenessDetector
from finger_detector import FingerDetector

# Server configuration
WEBSOCKET_HOST = "0.0.0.0"  # Listen on all interfaces for cloud deployment
WEBSOCKET_PORT = 8765
RESULT_DISPLAY_TIME = 3  # Seconds to show result before auto-restart

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LivenessWebSocketServer:
    """WebSocket server for liveness detection (frontend camera version)."""

    def __init__(self):
        """Initialize server."""
        logger.info("="*70)
        logger.info("        TRACK D: Cloud WebSocket Server")
        logger.info("        (Frontend Camera Version)")
        logger.info("="*70)

        # Validate configuration
        logger.info("Validating configuration...")
        config.validate_config()

        # Initialize components
        logger.info("Initializing components...")
        self.liveness_detector = LivenessDetector()
        self.finger_detector = FingerDetector()

        # Create output directory
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        logger.info(f"Output directory: {config.OUTPUT_DIR}/")

        # Server state
        self.analysis_active = False
        self.current_client = None
        self.saved_count = 0

        # Result timing
        self.result_timestamp = None
        self.auto_restart_enabled = True

        # Frame tracking
        self.last_frame = None
        self.frames_received = 0

        logger.info("✓ Server initialized!")

    async def handle_client(self, websocket, path):
        """
        Handle WebSocket client connection.

        Args:
            websocket: WebSocket connection
            path: Connection path
        """
        client_address = websocket.remote_address
        logger.info(f"[CONNECTED] Client: {client_address}")

        # Only allow one client at a time
        if self.current_client is not None:
            await websocket.send(json.dumps({
                "error": "Server busy - another client is connected"
            }))
            await websocket.close()
            logger.warning(f"[REJECTED] Client {client_address} - server busy")
            return

        self.current_client = websocket

        try:
            # Send welcome message
            await websocket.send(json.dumps({
                "type": "connection",
                "message": "Connected to TRACK D Cloud Server",
                "status": "ready",
                "version": "cloud-1.0",
                "commands": ["START_ANALYSIS", "RESET", "SAVE_RESULT", "STOP_ANALYSIS"],
                "note": "Send camera frames with type='frame'"
            }))

            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "command")

                    if msg_type == "frame":
                        # Frame data from frontend
                        await self.process_frame(websocket, data)

                    elif msg_type == "command" or "command" in data:
                        # Command message
                        command = data.get("command", "").upper()
                        logger.info(f"[COMMAND] Received: {command}")

                        if command == "START_ANALYSIS":
                            await self.start_analysis(websocket)

                        elif command == "RESET":
                            await self.reset_analysis(websocket)

                        elif command == "SAVE_RESULT":
                            await self.save_result(websocket)

                        elif command == "STOP_ANALYSIS":
                            await self.stop_analysis(websocket)

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
                    logger.error(f"[ERROR] Message handling: {e}")
                    traceback.print_exc()

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"[DISCONNECTED] Client: {client_address}")

        finally:
            # Cleanup
            self.current_client = None
            if self.analysis_active:
                self.analysis_active = False
                self.liveness_detector.reset()
            logger.info(f"[CLEANUP] Client {client_address} disconnected")

    async def start_analysis(self, websocket):
        """
        Start analysis session.

        Args:
            websocket: WebSocket connection
        """
        if self.analysis_active:
            await websocket.send(json.dumps({
                "type": "status",
                "message": "Analysis already active"
            }))
            return

        logger.info("[START] Starting analysis session...")

        # Reset detector
        self.liveness_detector.reset()
        self.frames_received = 0
        self.result_timestamp = None

        # Start analysis
        self.analysis_active = True

        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis started - send camera frames",
            "analysis_active": True
        }))

        logger.info("✓ Analysis session started")

    async def stop_analysis(self, websocket):
        """
        Stop analysis session.

        Args:
            websocket: WebSocket connection
        """
        logger.info("[STOP] Stopping analysis...")

        self.analysis_active = False
        self.liveness_detector.reset()

        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis stopped",
            "analysis_active": False
        }))

        logger.info("✓ Analysis stopped")

    async def reset_analysis(self, websocket):
        """
        Reset analysis to start fresh.

        Args:
            websocket: WebSocket connection
        """
        logger.info("[RESET] Resetting analysis...")

        self.liveness_detector.reset()
        self.result_timestamp = None
        self.frames_received = 0

        await websocket.send(json.dumps({
            "type": "status",
            "message": "Analysis reset"
        }))

        logger.info("✓ Analysis reset")

    async def process_frame(self, websocket, data):
        """
        Process frame from frontend.

        Args:
            websocket: WebSocket connection
            data: Frame data with base64 encoded image
        """
        if not self.analysis_active:
            # Ignore frames if not in analysis mode
            return

        try:
            # Decode frame
            frame_data = data.get("frame", "")

            # Remove data URL prefix if present
            if frame_data.startswith("data:image"):
                frame_data = frame_data.split(",")[1]

            frame_bytes = base64.b64decode(frame_data)
            frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

            if frame is None:
                logger.warning("[WARNING] Failed to decode frame")
                return

            self.frames_received += 1
            self.last_frame = frame

            # Detect finger
            finger_detected = self.finger_detector.is_finger_visible(frame)

            # Analyze frame
            result = self.liveness_detector.analyze_frame(frame, finger_detected)

            # Check for auto-restart
            if self.auto_restart_enabled and result['status'] in ['LIVE', 'SPOOF']:
                # Mark timestamp when result first appears
                if self.result_timestamp is None:
                    self.result_timestamp = datetime.now()
                    logger.info(f"[RESULT] {result['status']} - Auto-restart in {RESULT_DISPLAY_TIME}s")
                else:
                    # Check if display time elapsed
                    elapsed = (datetime.now() - self.result_timestamp).total_seconds()
                    if elapsed >= RESULT_DISPLAY_TIME:
                        logger.info("[AUTO-RESTART] Resetting for next person...")
                        self.liveness_detector.reset()
                        self.result_timestamp = None

            # Create response message
            response = self.create_message(result, finger_detected, self.frames_received)

            # Send to client
            await websocket.send(json.dumps(response))

            # Log periodically
            if self.frames_received % 30 == 0:
                logger.info(f"[FRAMES] Received: {self.frames_received}, Status: {result['status']}")

        except Exception as e:
            logger.error(f"[ERROR] Processing frame: {e}")
            traceback.print_exc()

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

        if self.last_frame is None:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "No frame available"
            }))
            return

        # Save to disk
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{config.OUTPUT_DIR}/trackd_{timestamp}_{self.saved_count}.png"

            cv2.imwrite(filename, self.last_frame)

            # Also save metadata
            metadata_file = f"{config.OUTPUT_DIR}/trackd_{timestamp}_{self.saved_count}.json"
            metadata = {
                "timestamp": timestamp,
                "result": "LIVE",
                "confidence": self.liveness_detector.confidence * 100,
                "scores": {k: v * 100 for k, v in self.liveness_detector.scores.items()}
            }

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            self.saved_count += 1

            await websocket.send(json.dumps({
                "type": "save_result",
                "message": "Result saved",
                "filename": filename,
                "metadata_file": metadata_file,
                "save_count": self.saved_count
            }))

            logger.info(f"✓ Result saved: {filename}")

        except Exception as e:
            await websocket.send(json.dumps({
                "type": "error",
                "message": f"Save failed: {str(e)}"
            }))
            logger.error(f"[ERROR] Save failed: {e}")

    def create_message(self, result, finger_detected, frame_count):
        """
        Create WebSocket message with detection data.

        Args:
            result: Analysis result from liveness detector
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

    logger.info(f"\n{'='*70}")
    logger.info(f"Server starting on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    logger.info(f"{'='*70}\n")

    logger.info("Configuration:")
    logger.info(f"  Mode: Cloud (Frontend Camera)")
    logger.info(f"  Auto-restart after result: {RESULT_DISPLAY_TIME}s")
    logger.info(f"  Host: {WEBSOCKET_HOST}")
    logger.info(f"  Port: {WEBSOCKET_PORT}")
    logger.info(f"\nWaiting for client connection...")
    logger.info(f"{'='*70}\n")

    async with websockets.serve(
        server.handle_client,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT,
        max_size=10 * 1024 * 1024  # 10MB max message size for large frames
    ):
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n[SHUTDOWN] Server stopped by user")
    except Exception as e:
        logger.error(f"\n[ERROR] Server crashed: {e}")
        traceback.print_exc()
