"""
UI Helper Module - SIMPLE VERSION
Just camera + result (LIVE/SPOOF with attack type)
"""

import cv2
import numpy as np
import config


class UIHelper:
    """
    Simple UI: Camera feed → LIVE/SPOOF result
    """
    
    def __init__(self):
        """Initialize UI helper."""
        self.font = config.FONT
        
    def draw_main_ui(self, frame, result):
        """
        Draw UI based on status.
        
        WAITING: Show "Show your finger" message
        ANALYZING: Camera with guide box
        LIVE/SPOOF: Show result with attack type
        
        Args:
            frame: BGR camera image
            result: Analysis result
        
        Returns:
            frame: Annotated frame
        """
        
        h, w = frame.shape[:2]
        
        if result['status'] == 'WAITING':
            # Waiting for finger
            display = self._draw_waiting(frame, result)
        elif result['status'] == 'ANALYZING':
            # Analyzing finger
            display = self._draw_analyzing(frame, result)
        else:
            # Result (LIVE/SPOOF)
            display = self._draw_result(frame, result)
        
        return display
    
    def _draw_waiting(self, frame, result):
        """
        Waiting phase: Show message to place finger.
        """
        
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Draw guide box
        self._draw_finger_guide(display)
        
        # Large message
        msg = "SHOW YOUR FINGER"
        text_size = cv2.getTextSize(msg, self.font, 1.2, 3)[0]
        text_x = (w - text_size[0]) // 2
        text_y = 60
        
        # Background
        cv2.rectangle(display,
                     (text_x - 20, text_y - 45),
                     (text_x + text_size[0] + 20, text_y + 10),
                     config.COLOR_BACKGROUND, -1)
        
        cv2.putText(display, msg, (text_x, text_y),
                   self.font, 1.2, config.COLOR_WARNING, 3)
        
        # Instruction
        inst = "Position your index finger in the frame"
        inst_size = cv2.getTextSize(inst, self.font, 0.7, 2)[0]
        inst_x = (w - inst_size[0]) // 2
        inst_y = h - 40
        
        cv2.putText(display, inst, (inst_x, inst_y),
                   self.font, 0.7, config.COLOR_TEXT, 2)
        
        return display
    
    def _draw_analyzing(self, frame, result):
        """
        Analyzing phase: Clean camera with guide box.
        """
        
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Draw guide box for finger placement
        self._draw_finger_guide(display)
        
        # Small status text at top
        status_text = "Analyzing..."
        cv2.putText(display, status_text, (20, 40),
                   self.font, 0.8, config.COLOR_ANALYZING, 2)
        
        return display
    
    def _draw_result(self, frame, result):
        """
        Result phase: Show LIVE or SPOOF with attack type.
        """
        
        display = frame.copy()
        h, w = display.shape[:2]
        
        # Semi-transparent overlay
        overlay = np.zeros((h, w, 3), dtype=np.uint8)
        overlay[:] = config.COLOR_BACKGROUND
        display = cv2.addWeighted(display, 0.3, overlay, 0.7, 0)
        
        if result['is_live']:
            self._draw_live_result(display, result)
        else:
            self._draw_spoof_result(display, result)
        
        return display
    
    def _draw_live_result(self, frame, result):
        """Draw LIVE result."""
        h, w = frame.shape[:2]
        
        # Large checkmark
        center = (w // 2, h // 2 - 80)
        radius = 100
        
        # Circle
        cv2.circle(frame, center, radius, config.COLOR_LIVE, 8)
        
        # Checkmark
        check_points = np.array([
            [center[0] - 40, center[1]],
            [center[0] - 15, center[1] + 35],
            [center[0] + 45, center[1] - 40]
        ], dtype=np.int32)
        cv2.polylines(frame, [check_points], False, config.COLOR_LIVE, 12)
        
        # "LIVE" text
        text = "LIVE"
        text_size = cv2.getTextSize(text, self.font, 2.5, 4)[0]
        text_x = (w - text_size[0]) // 2
        text_y = center[1] + 150
        
        cv2.putText(frame, text, (text_x, text_y),
                   self.font, 2.5, config.COLOR_LIVE, 4)
        
        # Confidence
        confidence = int(result['confidence'] * 100)
        conf_text = f"{confidence}% Confidence"
        conf_size = cv2.getTextSize(conf_text, self.font, 1.0, 2)[0]
        conf_x = (w - conf_size[0]) // 2
        conf_y = text_y + 60
        
        cv2.putText(frame, conf_text, (conf_x, conf_y),
                   self.font, 1.0, config.COLOR_TEXT, 2)
        
        # Controls
        self._draw_controls(frame, h - 60)
    
    def _draw_spoof_result(self, frame, result):
        """Draw SPOOF result with attack type."""
        h, w = frame.shape[:2]
        
        # Large X
        center = (w // 2, h // 2 - 80)
        radius = 100
        size = 60
        
        # Circle
        cv2.circle(frame, center, radius, config.COLOR_SPOOF, 8)
        
        # X
        cv2.line(frame,
                (center[0] - size, center[1] - size),
                (center[0] + size, center[1] + size),
                config.COLOR_SPOOF, 12)
        cv2.line(frame,
                (center[0] - size, center[1] + size),
                (center[0] + size, center[1] - size),
                config.COLOR_SPOOF, 12)
        
        # "SPOOF" text
        text = "SPOOF"
        text_size = cv2.getTextSize(text, self.font, 2.5, 4)[0]
        text_x = (w - text_size[0]) // 2
        text_y = center[1] + 150
        
        cv2.putText(frame, text, (text_x, text_y),
                   self.font, 2.5, config.COLOR_SPOOF, 4)
        
        # Attack type (subcategory)
        if result.get('attack_type'):
            attack_text = result['attack_type'].replace('_', ' ').title()
            
            # Full attack description
            attack_descriptions = {
                'Photo Attack': 'Printed Photo Detected',
                'Screen Attack': 'Phone/Screen Detected',
                'Video Replay': 'Video Playback Detected',
                'Fake Finger': 'Artificial Finger Detected'
            }
            
            attack_desc = attack_descriptions.get(attack_text, attack_text)
            
            # Background box
            desc_size = cv2.getTextSize(attack_desc, self.font, 0.9, 2)[0]
            box_w = desc_size[0] + 40
            box_h = 50
            box_x = (w - box_w) // 2
            box_y = text_y + 40
            
            # Draw box
            cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h),
                         config.COLOR_WARNING, -1)
            cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h),
                         config.COLOR_TEXT, 2)
            
            # Attack type text
            desc_x = (w - desc_size[0]) // 2
            desc_y = box_y + 33
            
            cv2.putText(frame, attack_desc, (desc_x, desc_y),
                       self.font, 0.9, config.COLOR_BACKGROUND, 2)
        else:
            # Generic spoof message
            generic_text = "Suspicious Pattern Detected"
            gen_size = cv2.getTextSize(generic_text, self.font, 0.9, 2)[0]
            gen_x = (w - gen_size[0]) // 2
            gen_y = text_y + 60
            
            cv2.putText(frame, generic_text, (gen_x, gen_y),
                       self.font, 0.9, config.COLOR_WARNING, 2)
        
        # Controls
        self._draw_controls(frame, h - 60)
    
    def _draw_finger_guide(self, frame):
        """Draw finger placement guide."""
        h, w = frame.shape[:2]
        
        # Guide box
        guide_w, guide_h = 350, 450
        guide_x = (w - guide_w) // 2
        guide_y = (h - guide_h) // 2
        
        # Dashed rectangle
        self._draw_dashed_rect(frame, guide_x, guide_y, guide_w, guide_h,
                              config.COLOR_ACCENT, 3)
        
        # Corner markers
        corner_len = 40
        thickness = 5
        
        # Top-left
        cv2.line(frame, (guide_x, guide_y), (guide_x + corner_len, guide_y),
                config.COLOR_ACCENT, thickness)
        cv2.line(frame, (guide_x, guide_y), (guide_x, guide_y + corner_len),
                config.COLOR_ACCENT, thickness)
        
        # Top-right
        cv2.line(frame, (guide_x + guide_w, guide_y), (guide_x + guide_w - corner_len, guide_y),
                config.COLOR_ACCENT, thickness)
        cv2.line(frame, (guide_x + guide_w, guide_y), (guide_x + guide_w, guide_y + corner_len),
                config.COLOR_ACCENT, thickness)
        
        # Bottom-left
        cv2.line(frame, (guide_x, guide_y + guide_h), (guide_x + corner_len, guide_y + guide_h),
                config.COLOR_ACCENT, thickness)
        cv2.line(frame, (guide_x, guide_y + guide_h), (guide_x, guide_y + guide_h - corner_len),
                config.COLOR_ACCENT, thickness)
        
        # Bottom-right
        cv2.line(frame, (guide_x + guide_w, guide_y + guide_h),
                (guide_x + guide_w - corner_len, guide_y + guide_h),
                config.COLOR_ACCENT, thickness)
        cv2.line(frame, (guide_x + guide_w, guide_y + guide_h),
                (guide_x + guide_w, guide_y + guide_h - corner_len),
                config.COLOR_ACCENT, thickness)
        
        # Text at top
        text = "Place finger in frame"
        text_size = cv2.getTextSize(text, self.font, 0.8, 2)[0]
        text_x = (w - text_size[0]) // 2
        text_y = guide_y - 20
        
        # Background for text
        bg_padding = 15
        cv2.rectangle(frame,
                     (text_x - bg_padding, text_y - 30),
                     (text_x + text_size[0] + bg_padding, text_y + 5),
                     config.COLOR_BACKGROUND, -1)
        
        cv2.putText(frame, text, (text_x, text_y),
                   self.font, 0.8, config.COLOR_ACCENT, 2)
    
    def _draw_controls(self, frame, y_pos):
        """Draw control hints."""
        h, w = frame.shape[:2]
        
        # Main control - RESTART
        restart_msg = "Press SPACE BAR to restart analysis"
        restart_size = cv2.getTextSize(restart_msg, self.font, 0.8, 2)[0]
        restart_x = (w - restart_size[0]) // 2
        restart_y = y_pos
        
        # Background box
        box_padding = 20
        cv2.rectangle(frame,
                     (restart_x - box_padding, restart_y - 35),
                     (restart_x + restart_size[0] + box_padding, restart_y + 10),
                     config.COLOR_ACCENT, -1)
        
        cv2.rectangle(frame,
                     (restart_x - box_padding, restart_y - 35),
                     (restart_x + restart_size[0] + box_padding, restart_y + 10),
                     config.COLOR_TEXT, 2)
        
        cv2.putText(frame, restart_msg, (restart_x, restart_y),
                   self.font, 0.8, config.COLOR_BACKGROUND, 2)
        
        # Other controls
        controls = [
            "Press 'S' to save result",
            "Press 'Q' to quit"
        ]
        
        for i, control in enumerate(controls):
            text_size = cv2.getTextSize(control, self.font, 0.5, 1)[0]
            text_x = (w - text_size[0]) // 2
            text_y = restart_y + 50 + (i * 25)
            
            cv2.putText(frame, control, (text_x, text_y),
                       self.font, 0.5, config.COLOR_TEXT, 1)
    
    def _draw_dashed_rect(self, frame, x, y, w, h, color, thickness):
        """Draw dashed rectangle."""
        dash_length = 15
        gap_length = 10
        
        # Top
        for i in range(x, x + w, dash_length + gap_length):
            cv2.line(frame, (i, y), (min(i + dash_length, x + w), y), color, thickness)
        
        # Bottom
        for i in range(x, x + w, dash_length + gap_length):
            cv2.line(frame, (i, y + h), (min(i + dash_length, x + w), y + h), color, thickness)
        
        # Left
        for i in range(y, y + h, dash_length + gap_length):
            cv2.line(frame, (x, i), (x, min(i + dash_length, y + h)), color, thickness)
        
        # Right
        for i in range(y, y + h, dash_length + gap_length):
            cv2.line(frame, (x + w, i), (x + w, min(i + dash_length, y + h)), color, thickness)


if __name__ == '__main__':
    """Test UI helper."""
    print("="*70)
    print("UI Helper Module - Simple Camera Version")
    print("="*70)
    print("\nFeatures:")
    print("  • Clean camera feed during analysis")
    print("  • Guide box for finger placement")
    print("  • LIVE/SPOOF result with attack type")
    print("  • No clutter, just essentials")
    print("\nModule ready!")