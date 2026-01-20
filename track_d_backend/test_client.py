"""
TRACK D - WebSocket Test Client
Local test client for WebSocket server

This client connects to the WebSocket server and displays
the camera feed with real-time detection results.

Usage:
1. Start server: python server.py
2. Run this client: python test_client.py

Controls:
- Press 'S' to send START_ANALYSIS command
- Press 'R' to send RESET command
- Press 'V' to send SAVE_RESULT command
- Press 'P' to PAUSE streaming (STOP_STREAM)
- Press 'U' to RESUME streaming (RESUME_STREAM)
- Press 'Q' to quit
"""

import asyncio
import websockets
import json
import cv2
import numpy as np
import base64
from datetime import datetime


class LivenessTestClient:
    """Test client for WebSocket server."""

    def __init__(self, server_url="ws://localhost:8765"):
        """
        Initialize test client.

        Args:
            server_url: WebSocket server URL
        """
        self.server_url = server_url
        self.websocket = None
        self.running = True
        self.current_frame = None
        self.current_data = None

        print("="*70)
        print("        TRACK D: Test Client")
        print("="*70)
        print(f"\nServer URL: {server_url}")
        print("\nControls:")
        print("  S - Start Analysis")
        print("  R - Reset")
        print("  V - Save Result")
        print("  P - Pause streaming")
        print("  U - Resume streaming (Unpause)")
        print("  Q - Quit")
        print("="*70 + "\n")

    async def connect(self):
        """Connect to WebSocket server."""
        print(f"[CONNECTING] {self.server_url}...")

        try:
            self.websocket = await websockets.connect(self.server_url)
            print("[CONNECTED] ✓\n")
            return True

        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    async def send_command(self, command):
        """
        Send command to server.

        Args:
            command: Command string
        """
        if self.websocket is None:
            print("[ERROR] Not connected")
            return

        message = json.dumps({"command": command})
        await self.websocket.send(message)
        print(f"[SENT] {command}")

    async def receive_messages(self):
        """Receive and process messages from server."""
        print("[RECEIVING] Listening for messages...\n")

        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    # Handle different message types
                    msg_type = data.get("type", "data")

                    if msg_type == "connection":
                        print(f"[SERVER] {data.get('message')}")
                        print(f"  Available commands: {data.get('commands')}\n")

                    elif msg_type == "status":
                        print(f"[STATUS] {data.get('message')}")

                    elif msg_type == "error":
                        print(f"[ERROR] {data.get('message')}")

                    elif msg_type == "save_result":
                        print(f"[SAVED] {data.get('filename')}")
                        print(f"  Total saved: {data.get('save_count')}\n")

                    else:
                        # Regular data message with frame
                        self.process_data(data)

                except json.JSONDecodeError as e:
                    print(f"[ERROR] Invalid JSON: {e}")

                except Exception as e:
                    print(f"[ERROR] Processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            print("\n[DISCONNECTED] Connection closed")
            self.running = False

    def process_data(self, data):
        """
        Process detection data and display frame.

        Args:
            data: Detection data dictionary
        """
        self.current_data = data

        # Decode frame
        if "frame" in data:
            try:
                frame_data = base64.b64decode(data["frame"])
                frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

                if frame is not None:
                    # Draw detection info on frame
                    annotated_frame = self.draw_info(frame, data)
                    self.current_frame = annotated_frame

            except Exception as e:
                print(f"[ERROR] Decoding frame: {e}")

        # Print detection info periodically
        frame_count = data.get("frame_count", 0)
        if frame_count % 30 == 0:  # Every 30 frames (~1 second at 30 FPS)
            self.print_detection_info(data)

    def draw_info(self, frame, data):
        """
        Draw detection information on frame.

        Args:
            frame: OpenCV frame
            data: Detection data

        Returns:
            Annotated frame
        """
        h, w = frame.shape[:2]

        # Status color
        status = data.get("status", "WAITING")
        if status == "LIVE":
            color = (100, 200, 100)  # Green
        elif status == "SPOOF":
            color = (80, 80, 220)  # Red
        elif status == "ANALYZING":
            color = (220, 180, 100)  # Blue
        else:
            color = (200, 200, 200)  # Gray

        # Draw status bar at top
        cv2.rectangle(frame, (0, 0), (w, 60), (40, 40, 40), -1)

        # Status text
        cv2.putText(frame, f"Status: {status}", (20, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

        # Confidence
        confidence = data.get("confidence", 0)
        cv2.putText(frame, f"{confidence:.1f}%", (w - 150, 35),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

        # Finger detection indicator
        finger_detected = data.get("finger_detected", False)
        finger_color = (100, 200, 100) if finger_detected else (100, 100, 100)
        cv2.circle(frame, (w - 30, 30), 15, finger_color, -1)

        # Instruction at bottom
        instruction = data.get("ui_elements", {}).get("instruction", "")
        cv2.rectangle(frame, (0, h - 60), (w, h), (40, 40, 40), -1)
        cv2.putText(frame, instruction, (20, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2)

        # Progress bar
        progress = data.get("ui_elements", {}).get("progress", 0)
        if progress > 0:
            bar_width = int((w - 40) * (progress / 100))
            cv2.rectangle(frame, (20, h - 50), (20 + bar_width, h - 40), color, -1)

        # Scores panel (right side)
        scores = data.get("scores", {})
        y_offset = 80

        cv2.putText(frame, "Scores:", (w - 200, y_offset),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        y_offset += 25

        for score_name, score_value in scores.items():
            if score_name == "overall":
                continue

            text = f"{score_name[:6]}: {score_value:.0f}"
            cv2.putText(frame, text, (w - 200, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
            y_offset += 20

        # Overall score (larger)
        overall = scores.get("overall", 0)
        cv2.putText(frame, f"Overall: {overall:.1f}", (w - 200, y_offset + 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Attack type if detected
        attack_type = data.get("attack_type")
        if attack_type:
            cv2.rectangle(frame, (20, 80), (w - 20, 130), (60, 60, 220), 2)
            cv2.putText(frame, f"Attack: {attack_type}", (30, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 60, 220), 2)

        return frame

    def print_detection_info(self, data):
        """
        Print detection information to console.

        Args:
            data: Detection data
        """
        print(f"\n{'='*60}")
        print(f"Frame: {data.get('frame_count', 0)}")
        print(f"Timestamp: {data.get('timestamp', '')}")
        print(f"Status: {data.get('status', 'UNKNOWN')}")
        print(f"Finger Detected: {data.get('finger_detected', False)}")
        print(f"Confidence: {data.get('confidence', 0):.2f}%")

        if data.get('result'):
            print(f"Result: {data.get('result')}")

        if data.get('attack_type'):
            print(f"Attack Type: {data.get('attack_type')}")

        print(f"\nScores:")
        scores = data.get('scores', {})
        for name, value in scores.items():
            print(f"  {name}: {value:.2f}")

        print(f"\nInstruction: {data.get('ui_elements', {}).get('instruction', '')}")
        print(f"Progress: {data.get('ui_elements', {}).get('progress', 0):.1f}%")
        print(f"{'='*60}")

    async def handle_keyboard(self):
        """Handle keyboard input for commands."""
        # Note: This runs in a separate task
        # OpenCV window will handle key presses

    async def display_loop(self):
        """Display frames in OpenCV window."""
        window_name = "TRACK D - Test Client"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

        print("[DISPLAY] Window opened\n")

        while self.running:
            if self.current_frame is not None:
                cv2.imshow(window_name, self.current_frame)

            # Handle key presses
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == ord('Q'):
                print("\n[QUIT] Stopping client...")
                self.running = False
                break

            elif key == ord('s') or key == ord('S'):
                await self.send_command("START_ANALYSIS")

            elif key == ord('r') or key == ord('R'):
                await self.send_command("RESET")

            elif key == ord('v') or key == ord('V'):
                await self.send_command("SAVE_RESULT")

            elif key == ord('p') or key == ord('P'):
                await self.send_command("STOP_STREAM")

            elif key == ord('u') or key == ord('U'):
                await self.send_command("RESUME_STREAM")

            await asyncio.sleep(0.01)

        cv2.destroyAllWindows()
        print("[DISPLAY] Window closed")

    async def run(self):
        """Run the test client."""
        # Connect to server
        if not await self.connect():
            return

        # Run receive and display loops concurrently
        try:
            await asyncio.gather(
                self.receive_messages(),
                self.display_loop()
            )

        except Exception as e:
            print(f"\n[ERROR] Client error: {e}")

        finally:
            if self.websocket:
                await self.websocket.close()
                print("\n[CLOSED] WebSocket connection closed")


async def main():
    """Main entry point."""
    client = LivenessTestClient()
    await client.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Client stopped by user")
    except Exception as e:
        print(f"\n\n[ERROR] Client crashed: {e}")
        import traceback
        traceback.print_exc()
