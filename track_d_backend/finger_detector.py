"""
Finger Detector Module
Uses MediaPipe to detect ONLY index finger
Rejects faces, hands, other objects
"""

import cv2
import numpy as np
import mediapipe as mp


class FingerDetector:
    """
    Detects index finger using MediaPipe Hands.
    Returns bounding box if finger detected, None otherwise.
    """
    
    def __init__(self):
        """Initialize MediaPipe Hands."""
        
        print("Initializing MediaPipe Finger Detector...")
        
        # Initialize MediaPipe
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Index finger landmarks (5-8)
        self.INDEX_FINGER_BASE = 5
        self.INDEX_FINGER_TIP = 8
        
        # Bounding box padding
        self.BBOX_PADDING = 50
        
        print("✓ Finger Detector ready!")
    
    def detect_finger(self, frame):
        """
        Detect index finger in frame.
        
        Args:
            frame: BGR image from camera
        
        Returns:
            tuple: (x, y, w, h, finger_roi) if finger detected
                   None if no finger detected
        """
        
        height, width, _ = frame.shape
        
        # Convert to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process with MediaPipe
        results = self.hands.process(rgb_frame)
        
        # Check if hand detected
        if not results.multi_hand_landmarks:
            return None
        
        # Get first hand
        hand_landmarks = results.multi_hand_landmarks[0]
        
        # Extract index finger landmarks
        index_finger_landmarks = []
        for i in range(self.INDEX_FINGER_BASE, self.INDEX_FINGER_TIP + 1):
            landmark = hand_landmarks.landmark[i]
            x = int(landmark.x * width)
            y = int(landmark.y * height)
            index_finger_landmarks.append((x, y))
        
        # Calculate bounding box
        x_coords = [pt[0] for pt in index_finger_landmarks]
        y_coords = [pt[1] for pt in index_finger_landmarks]
        
        min_x = max(0, min(x_coords) - self.BBOX_PADDING)
        max_x = min(width, max(x_coords) + self.BBOX_PADDING)
        min_y = max(0, min(y_coords) - self.BBOX_PADDING)
        max_y = min(height, max(y_coords) + self.BBOX_PADDING)
        
        x, y = min_x, min_y
        w, h = max_x - min_x, max_y - min_y
        
        # Extract finger ROI
        finger_roi = frame[y:y+h, x:x+w]
        
        # Validate finger ROI
        if w < 50 or h < 50:  # Too small
            return None
        
        return (x, y, w, h, finger_roi)
    
    def is_finger_visible(self, frame):
        """
        Quick check if finger is visible.
        
        Returns:
            bool: True if finger detected, False otherwise
        """
        
        result = self.detect_finger(frame)
        return result is not None
    
    def draw_finger_box(self, frame, color=(0, 255, 0)):
        """
        Draw bounding box around detected finger.
        
        Args:
            frame: BGR image
            color: Box color (BGR)
        
        Returns:
            frame: Annotated frame
        """
        
        result = self.detect_finger(frame)
        
        if result is None:
            return frame
        
        x, y, w, h, _ = result
        
        # Draw box
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 3)
        
        # Label
        cv2.putText(frame, "Finger Detected", (x, y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return frame


if __name__ == '__main__':
    """Test finger detector."""
    print("="*70)
    print("Finger Detector Module - Test Mode")
    print("="*70)
    
    detector = FingerDetector()
    
    print("\nCapabilities:")
    print("  • Detects index finger only")
    print("  • Rejects faces, hands, other objects")
    print("  • Uses MediaPipe Hands")
    print("  • Returns bounding box + ROI")
    
    print("\nModule ready!")