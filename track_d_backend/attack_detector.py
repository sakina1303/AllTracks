"""
Attack Detector Module
Detects specific types of spoofing attacks

Attack Types:
1. Photo Attack - Printed fingerprint photo
2. Screen Attack - Phone/tablet display
3. Video Replay - Recorded video playback
4. Fake Finger - Silicone/rubber replica
"""

import cv2
import numpy as np
from collections import deque
import config


class AttackDetector:
    """
    Detects specific types of spoofing attacks.
    """
    
    def __init__(self):
        """Initialize attack detector."""
        
        # Attack indicators
        self.attacks = {
            'photo_attack': False,
            'screen_attack': False,
            'video_replay': False,
            'fake_finger': False
        }
        
        # Detection confidence for each attack
        self.attack_confidence = {
            'photo_attack': 0.0,
            'screen_attack': 0.0,
            'video_replay': 0.0,
            'fake_finger': 0.0
        }
        
        # History for video replay detection
        self.brightness_history = deque(maxlen=20)
        self.pattern_history = deque(maxlen=10)
        
    def reset(self):
        """Reset attack detection state."""
        self.attacks = {k: False for k in self.attacks.keys()}
        self.attack_confidence = {k: 0.0 for k in self.attack_confidence.keys()}
        self.brightness_history.clear()
        self.pattern_history.clear()
    
    def detect_photo_attack(self, motion_score, texture_score, gray):
        """
        Detect if input is a printed photo.
        
        Indicators:
        - Very low motion (paper doesn't move naturally)
        - Low texture complexity
        - Regular print patterns
        
        Args:
            motion_score: Motion detection score (0-1)
            texture_score: Texture analysis score (0-1)
            gray: Grayscale image
        
        Returns:
            tuple: (is_photo_attack, confidence)
        """
        
        confidence = 0.0
        
        # Indicator 1: Very low motion
        if motion_score < 0.2:
            confidence += 0.4
        
        # Indicator 2: Low texture
        if texture_score < config.PHOTO_ATTACK_TEXTURE_MAX:
            confidence += 0.3
        
        # Indicator 3: Check for print patterns
        has_print_pattern = self._detect_print_pattern(gray)
        if has_print_pattern:
            confidence += 0.3
        
        is_attack = confidence >= 0.5
        
        self.attacks['photo_attack'] = is_attack
        self.attack_confidence['photo_attack'] = confidence
        
        return is_attack, confidence
    
    def detect_screen_attack(self, color_variance, pattern_score, frame):
        """
        Detect if input is from a phone/tablet screen.
        
        Indicators:
        - Low color variance (backlight uniformity)
        - Regular pixel grid patterns
        - Screen refresh artifacts
        
        Args:
            color_variance: Color variance score (0-1)
            pattern_score: Pattern detection score (0-1)
            frame: BGR image
        
        Returns:
            tuple: (is_screen_attack, confidence)
        """
        
        confidence = 0.0
        
        # Indicator 1: Low color variance
        if color_variance < 0.3:
            confidence += 0.3
        
        # Indicator 2: Regular patterns detected
        if pattern_score < 0.4:  # Low score = patterns found
            confidence += 0.3
        
        # Indicator 3: Check for screen characteristics
        has_screen_char = self._detect_screen_characteristics(frame)
        if has_screen_char:
            confidence += 0.4
        
        is_attack = confidence >= 0.5
        
        self.attacks['screen_attack'] = is_attack
        self.attack_confidence['screen_attack'] = confidence
        
        return is_attack, confidence
    
    def detect_video_replay(self, consistency_score, gray):
        """
        Detect if input is a recorded video playback.
        
        Indicators:
        - Repetitive patterns (video loops)
        - Sudden brightness jumps (video restarts)
        - Inconsistent frame-to-frame changes
        
        Args:
            consistency_score: Consistency check score (0-1)
            gray: Grayscale image
        
        Returns:
            tuple: (is_video_replay, confidence)
        """
        
        confidence = 0.0
        
        # Track brightness
        brightness = np.mean(gray)
        self.brightness_history.append(brightness)
        
        if len(self.brightness_history) >= 10:
            
            # Indicator 1: Check for sudden jumps (video loop restart)
            jumps = []
            for i in range(1, len(self.brightness_history)):
                diff = abs(self.brightness_history[i] - self.brightness_history[i-1])
                jumps.append(diff)
            
            max_jump = max(jumps) if jumps else 0
            if max_jump > config.VIDEO_REPLAY_JUMP_MIN:
                confidence += 0.4
            
            # Indicator 2: Check for repetitive patterns
            if self._detect_repetition():
                confidence += 0.4
        
        # Indicator 3: Low consistency score
        if consistency_score < 0.4:
            confidence += 0.2
        
        is_attack = confidence >= 0.5
        
        self.attacks['video_replay'] = is_attack
        self.attack_confidence['video_replay'] = confidence
        
        return is_attack, confidence
    
    def detect_fake_finger(self, edge_density, texture_score, gray):
        """
        Detect if input is a fake finger (silicone/rubber).
        
        Indicators:
        - Abnormal edge density (too smooth or too rough)
        - Unnatural texture
        - Missing skin characteristics
        
        Args:
            edge_density: Edge density score (0-1)
            texture_score: Texture analysis score (0-1)
            gray: Grayscale image
        
        Returns:
            tuple: (is_fake_finger, confidence)
        """
        
        confidence = 0.0
        
        # Indicator 1: Abnormal edge density
        if edge_density < 0.3 or edge_density > 0.8:
            confidence += 0.4
        
        # Indicator 2: Unusual texture
        if texture_score < 0.4:
            confidence += 0.3
        
        # Indicator 3: Check for skin-specific features
        has_skin_features = self._check_skin_features(gray)
        if not has_skin_features:
            confidence += 0.3
        
        is_attack = confidence >= 0.5
        
        self.attacks['fake_finger'] = is_attack
        self.attack_confidence['fake_finger'] = confidence
        
        return is_attack, confidence
    
    def get_primary_attack(self):
        """
        Get the most likely attack type.
        
        Returns:
            tuple: (attack_name, confidence) or (None, 0.0)
        """
        
        if not any(self.attacks.values()):
            return None, 0.0
        
        # Find attack with highest confidence
        max_attack = max(self.attack_confidence.items(), key=lambda x: x[1])
        
        if max_attack[1] >= 0.5:
            return max_attack
        
        return None, 0.0
    
    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _detect_print_pattern(self, gray):
        """
        Detect regular print patterns using FFT.
        
        Returns:
            bool: True if print pattern detected
        """
        
        # Resize for faster computation
        small = cv2.resize(gray, (config.FFT_SIZE, config.FFT_SIZE))
        
        # Apply FFT
        f = np.fft.fft2(small)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        # Remove DC component
        h, w = magnitude.shape
        r = config.FFT_DC_REMOVAL
        magnitude[h//2-r:h//2+r, w//2-r:w//2+r] = 0
        
        # Look for strong peaks (regular patterns)
        max_mag = np.max(magnitude)
        mean_mag = np.mean(magnitude)
        
        ratio = max_mag / (mean_mag + 1)
        
        # High ratio indicates regular patterns
        return ratio > config.FFT_PATTERN_THRESHOLD
    
    def _detect_screen_characteristics(self, frame):
        """
        Detect characteristics specific to screen displays.
        
        Returns:
            bool: True if screen characteristics detected
        """
        
        # Convert to HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Check saturation uniformity (screens have uniform backlight)
        s_channel = hsv[:, :, 1]
        s_std = np.std(s_channel)
        
        # Low saturation variance = screen
        if s_std < 20:
            return True
        
        # Check for RGB channel correlation (screens have high correlation)
        b, g, r = cv2.split(frame)
        corr_bg = np.corrcoef(b.flatten(), g.flatten())[0, 1]
        corr_gr = np.corrcoef(g.flatten(), r.flatten())[0, 1]
        
        avg_corr = (corr_bg + corr_gr) / 2
        
        # High correlation = screen
        return avg_corr > 0.9
    
    def _detect_repetition(self):
        """
        Detect if brightness pattern repeats (video loop).
        
        Returns:
            bool: True if repetition detected
        """
        
        if len(self.brightness_history) < 15:
            return False
        
        # Check if second half correlates with first half
        mid = len(self.brightness_history) // 2
        first_half = list(self.brightness_history)[:mid]
        second_half = list(self.brightness_history)[mid:mid*2]
        
        if len(first_half) != len(second_half):
            return False
        
        # Calculate correlation
        correlation = np.corrcoef(first_half, second_half)[0, 1]
        
        # High correlation = repetition
        return correlation > config.VIDEO_REPLAY_REPEAT_THRESHOLD
    
    def _check_skin_features(self, gray):
        """
        Check for skin-specific features.
        Real skin has specific texture properties.
        
        Returns:
            bool: True if skin features present
        """
        
        # Check local texture variation
        # Real skin has natural pores, hair follicles
        
        # Divide into patches
        h, w = gray.shape
        patch_size = 32
        
        if h < patch_size * 2 or w < patch_size * 2:
            return True  # Too small to analyze
        
        variances = []
        
        for i in range(0, h - patch_size, patch_size):
            for j in range(0, w - patch_size, patch_size):
                patch = gray[i:i+patch_size, j:j+patch_size]
                variances.append(np.var(patch))
        
        # Real skin has varied local variance
        variance_of_variances = np.var(variances)
        
        # Low variance-of-variances = artificial (too uniform)
        return variance_of_variances > 50
    
    def get_attack_summary(self):
        """
        Get summary of all detected attacks.
        
        Returns:
            dict: Attack summary with confidences
        """
        
        return {
            'any_attack_detected': any(self.attacks.values()),
            'attacks': self.attacks.copy(),
            'confidences': self.attack_confidence.copy(),
            'primary_attack': self.get_primary_attack()
        }


if __name__ == '__main__':
    """Test attack detector."""
    print("="*70)
    print("Attack Detector Module - Test Mode")
    print("="*70)
    
    detector = AttackDetector()
    
    print("\nAttack Types Detected:")
    for attack in detector.attacks.keys():
        print(f"  • {attack.replace('_', ' ').title()}")
    
    print("\nModule ready!")