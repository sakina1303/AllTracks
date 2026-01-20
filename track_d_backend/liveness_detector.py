"""
Liveness Detector - Core Module
Main liveness detection engine combining all methods

Methods:
1. Motion Detection - Natural hand tremor
2. Texture Analysis - Print/screen pattern detection
3. Consistency Check - Video replay detection
4. Edge Density - Fake finger detection
5. Color Variance - Screen detection
6. Pattern Detection - Print pattern detection
"""

import cv2
import numpy as np
from collections import deque
import config
from attack_detector import AttackDetector


class LivenessDetector:
    """
    Core liveness detection engine.
    Combines multiple detection methods for robust anti-spoofing.
    """
    
    def __init__(self):
        """Initialize liveness detector."""
        
        print("Initializing Liveness Detector...")
        
        # Frame buffers
        self.frame_buffer = deque(maxlen=config.MOTION_FRAMES)
        self.gray_buffer = deque(maxlen=config.MOTION_FRAMES)
        
        # Motion tracking
        self.motion_history = deque(maxlen=20)
        
        # Attack detector
        self.attack_detector = AttackDetector()
        
        # Analysis state
        self.frames_analyzed = 0
        self.is_live = False
        self.confidence = 0.0
        self.final_decision_made = False
        self.analysis_started = False  # NEW: Track if analysis has started
        
        # Individual scores
        self.scores = {
            'motion': 0.0,
            'texture': 0.0,
            'consistency': 0.0,
            'edge_density': 0.0,
            'color_variance': 0.0,
            'pattern_detection': 0.0
        }
        
        # Instructions for user
        self.current_instruction = config.INSTRUCTIONS['initial']
        
        print("✓ Liveness Detector ready!")
    
    def reset(self):
        """Reset all detection state."""
        self.frame_buffer.clear()
        self.gray_buffer.clear()
        self.motion_history.clear()
        self.attack_detector.reset()
        
        self.frames_analyzed = 0
        self.is_live = False
        self.confidence = 0.0
        self.final_decision_made = False
        self.analysis_started = False  # NEW: Reset analysis started flag
        
        self.scores = {k: 0.0 for k in self.scores.keys()}
        self.current_instruction = config.INSTRUCTIONS['initial']
        
        if config.DEBUG_MODE:
            print("[DEBUG] Detector reset")
    
    def analyze_frame(self, frame, finger_detected=False):
        """
        Main analysis function - analyzes single frame.
        
        Args:
            frame: BGR image from camera
            finger_detected: Whether finger is detected in frame
        
        Returns:
            dict: Analysis result
        """
        
        # If decision already made, stay on result screen
        # Don't reset until user presses 'R'
        if self.final_decision_made:
            status = 'LIVE' if self.is_live else 'SPOOF'
            instruction = self.current_instruction
            
            return self._create_result(
                status=status,
                progress=100,
                instruction=instruction,
                overall_score=self.confidence,
                attack_type=self._get_attack_type()
            )
        
        # If no finger detected, reset and wait
        if not finger_detected:
            # Reset analysis if it was started but not completed
            if self.analysis_started and not self.final_decision_made:
                self.reset()
            
            return self._create_result(
                status='WAITING',
                progress=0,
                instruction='Show your index finger to camera'
            )
        
        # Finger detected - start analysis if not started
        if not self.analysis_started:
            self.analysis_started = True
            self.frames_analyzed = 0  # Reset counter
            print("\n[ANALYSIS STARTED] Finger detected, analyzing...")
        
        self.frames_analyzed += 1
        
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Store frames
        self.frame_buffer.append(frame.copy())
        self.gray_buffer.append(gray)
        
        # Calculate progress
        progress = min(100, (self.frames_analyzed / config.MIN_FRAMES_FOR_DECISION) * 100)
        
        # Need minimum frames for analysis
        if len(self.frame_buffer) < 3:
            return self._create_result(
                status='ANALYZING',
                progress=progress,
                instruction=config.INSTRUCTIONS['collecting']
            )
        
        # ==========================================
        # PERFORM ALL DETECTION METHODS
        # ==========================================
        
        # 1. Motion Detection
        motion_score = self._detect_motion()
        self.scores['motion'] = motion_score
        
        # 2. Texture Analysis
        texture_score = self._analyze_texture(frame, gray)
        self.scores['texture'] = texture_score
        
        # 3. Consistency Check
        consistency_score = self._check_consistency()
        self.scores['consistency'] = consistency_score
        
        # 4. Edge Density Analysis
        edge_score = self._analyze_edge_density(gray)
        self.scores['edge_density'] = edge_score
        
        # 5. Color Variance Analysis
        color_score = self._analyze_color_variance(frame)
        self.scores['color_variance'] = color_score
        
        # 6. Pattern Detection
        pattern_score = self._detect_patterns(gray)
        self.scores['pattern_detection'] = pattern_score
        
        # ==========================================
        # CALCULATE OVERALL SCORE
        # ==========================================
        
        overall_score = self._calculate_overall_score()
        
        # ==========================================
        # DETECT SPECIFIC ATTACKS
        # ==========================================
        
        self.attack_detector.detect_photo_attack(motion_score, texture_score, gray)
        self.attack_detector.detect_screen_attack(color_score, pattern_score, frame)
        self.attack_detector.detect_video_replay(consistency_score, gray)
        self.attack_detector.detect_fake_finger(edge_score, texture_score, gray)
        
        attack_summary = self.attack_detector.get_attack_summary()
        
        # ==========================================
        # MAKE DECISION
        # ==========================================
        
        if not self.final_decision_made and self.frames_analyzed >= config.MIN_FRAMES_FOR_DECISION:
            
            print(f"\n[DECISION TIME] Frames analyzed: {self.frames_analyzed}")
            print(f"Overall score: {overall_score:.2f}")
            print(f"Color variance score: {color_score:.2f}")
            
            # CRITICAL: Enhanced Screen Detection
            is_screen = self._comprehensive_screen_check(frame, color_score)
            
            if is_screen:
                self.is_live = False
                self.confidence = 0.3  # Low confidence = screen detected
                self.final_decision_made = True
                status = 'SPOOF'
                instruction = config.INSTRUCTIONS['screen_attack']
                
                print("[DECISION] SPOOF - Phone/Screen detected!")
                
                # Force screen attack detection
                self.attack_detector.attacks['screen_attack'] = True
                
            elif config.SCREEN_VETO_ENABLED and color_score < config.SCREEN_VETO_THRESHOLD:
                # Fallback screen veto check
                self.is_live = False
                self.confidence = color_score
                self.final_decision_made = True
                status = 'SPOOF'
                instruction = config.INSTRUCTIONS['screen_attack']
                
                print("[DECISION] SPOOF - Low color variance (screen indicator)!")
                
                # Force screen attack detection
                self.attack_detector.attacks['screen_attack'] = True
                
            else:
                # Normal decision based on overall score
                self.is_live = overall_score >= config.LIVENESS_THRESHOLD
                self.confidence = overall_score
                self.final_decision_made = True
                
                if self.is_live:
                    status = 'LIVE'
                    instruction = config.INSTRUCTIONS['live_detected']
                    print(f"[DECISION] LIVE - Confidence: {overall_score:.2f}")
                else:
                    status = 'SPOOF'
                    # Get specific attack instruction
                    primary_attack, _ = attack_summary['primary_attack']
                    if primary_attack:
                        instruction = config.INSTRUCTIONS.get(primary_attack, 
                                                             config.INSTRUCTIONS['spoof_detected'])
                    else:
                        instruction = config.INSTRUCTIONS['spoof_detected']
                    
                    print(f"[DECISION] SPOOF - Score too low: {overall_score:.2f}")
        else:
            # Still analyzing
            status = 'ANALYZING'
            instruction = self._get_dynamic_instruction(overall_score, motion_score)
        
        self.current_instruction = instruction
        
        # ==========================================
        # PRINT SCORES (if enabled)
        # ==========================================
        
        if config.PRINT_SCORES and self.frames_analyzed % 5 == 0:
            self._print_scores(overall_score)
        
        return self._create_result(
            status=status,
            progress=progress,
            instruction=instruction,
            overall_score=overall_score,
            attack_type=attack_summary['primary_attack'][0] if attack_summary['primary_attack'][0] else None
        )
    
    # ==========================================
    # DETECTION METHODS
    # ==========================================
    
    def _detect_motion(self):
        """
        Motion-based detection using frame differencing.
        
        Real finger: Natural hand tremor causes pixel changes
        Photo/Screen: Completely static
        
        Returns:
            float: Motion score (0-1)
        """
        
        if len(self.gray_buffer) < 2:
            return 0.0
        
        motion_values = []
        
        # Compare recent frames
        for i in range(1, min(len(self.gray_buffer), 5)):
            prev = self.gray_buffer[i-1]
            curr = self.gray_buffer[i]
            
            # Calculate absolute difference
            diff = cv2.absdiff(prev, curr)
            
            # Count motion pixels
            motion_pixels = np.sum(diff > config.MOTION_PIXEL_THRESHOLD)
            motion_values.append(motion_pixels)
        
        avg_motion = np.mean(motion_values)
        self.motion_history.append(avg_motion)
        
        # Normalize score
        if avg_motion >= config.MOTION_THRESHOLD_OPTIMAL:
            score = 1.0
        elif avg_motion >= config.MOTION_THRESHOLD_MIN:
            # Scale between min and optimal
            score = 0.3 + 0.7 * (avg_motion - config.MOTION_THRESHOLD_MIN) / \
                   (config.MOTION_THRESHOLD_OPTIMAL - config.MOTION_THRESHOLD_MIN)
        else:
            # Below minimum (likely spoof)
            score = (avg_motion / config.MOTION_THRESHOLD_MIN) * 0.3
        
        return min(1.0, max(0.0, score))
    
    def _analyze_texture(self, frame, gray):
        """
        Texture analysis to detect prints and artificial surfaces.
        
        Args:
            frame: BGR image
            gray: Grayscale image
        
        Returns:
            float: Texture score (0-1)
        """
        
        # 1. Texture variance
        variance = np.var(gray)
        if variance >= config.TEXTURE_VARIANCE_OPTIMAL:
            variance_score = 1.0
        elif variance >= config.TEXTURE_VARIANCE_MIN:
            variance_score = 0.5 + 0.5 * (variance - config.TEXTURE_VARIANCE_MIN) / \
                           (config.TEXTURE_VARIANCE_OPTIMAL - config.TEXTURE_VARIANCE_MIN)
        else:
            variance_score = (variance / config.TEXTURE_VARIANCE_MIN) * 0.5
        
        # 2. High-frequency content (edge energy)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        hf_energy = np.var(laplacian)
        
        if hf_energy >= config.HF_CONTENT_OPTIMAL:
            hf_score = 1.0
        elif hf_energy >= config.HF_CONTENT_MIN:
            hf_score = 0.5 + 0.5 * (hf_energy - config.HF_CONTENT_MIN) / \
                      (config.HF_CONTENT_OPTIMAL - config.HF_CONTENT_MIN)
        else:
            hf_score = (hf_energy / config.HF_CONTENT_MIN) * 0.5
        
        # 3. Local texture diversity
        diversity_score = self._compute_texture_diversity(gray)
        
        # Combine scores
        texture_score = (
            variance_score * 0.4 +
            hf_score * 0.4 +
            diversity_score * 0.2
        )
        
        return min(1.0, max(0.0, texture_score))
    
    def _compute_texture_diversity(self, gray):
        """
        Compute local texture diversity.
        Real skin has diverse local patterns.
        
        Args:
            gray: Grayscale image
        
        Returns:
            float: Diversity score (0-1)
        """
        
        # Compute gradients
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Gradient magnitude
        gradient_mag = np.sqrt(gx**2 + gy**2)
        
        # Measure diversity (standard deviation)
        diversity = np.std(gradient_mag)
        
        # Normalize
        score = min(1.0, diversity / config.LBP_DIVERSITY_MIN)
        
        return score
    
    def _check_consistency(self):
        """
        Multi-frame consistency check.
        Real finger: Smooth, gradual changes
        Video replay: Sudden jumps, loops
        
        Returns:
            float: Consistency score (0-1)
        """
        
        if len(self.gray_buffer) < config.CONSISTENCY_WINDOW:
            return 0.5  # Neutral until enough frames
        
        # Calculate brightness for each frame
        brightness_values = [np.mean(frame) for frame in list(self.gray_buffer)[-config.CONSISTENCY_WINDOW:]]
        
        # Calculate frame-to-frame differences
        differences = []
        for i in range(1, len(brightness_values)):
            diff = abs(brightness_values[i] - brightness_values[i-1])
            differences.append(diff)
        
        avg_diff = np.mean(differences)
        max_diff = np.max(differences)
        
        # Check for sudden jumps (video loop restart)
        if max_diff > config.FRAME_JUMP_THRESHOLD:
            return 0.2  # Very low score for detected jump
        
        # Score based on average difference
        if avg_diff < config.CONSISTENCY_THRESHOLD:
            score = 1.0
        else:
            score = max(0.0, 1.0 - (avg_diff - config.CONSISTENCY_THRESHOLD) / 50)
        
        return score
    
    def _analyze_edge_density(self, gray):
        """
        Edge density analysis for fake finger detection.
        
        Args:
            gray: Grayscale image
        
        Returns:
            float: Edge score (0-1)
        """
        
        # Detect edges
        edges = cv2.Canny(gray, config.CANNY_THRESHOLD_LOW, config.CANNY_THRESHOLD_HIGH)
        
        # Calculate edge density
        edge_density = np.sum(edges > 0) / edges.size
        
        # Real skin has moderate edge density
        if config.EDGE_DENSITY_MIN <= edge_density <= config.EDGE_DENSITY_MAX:
            score = 1.0
        elif edge_density < config.EDGE_DENSITY_MIN:
            # Too few edges (smooth fake finger)
            score = edge_density / config.EDGE_DENSITY_MIN
        else:
            # Too many edges (rough fake or print)
            excess = edge_density - config.EDGE_DENSITY_MAX
            score = max(0.0, 1.0 - (excess / 0.3))
        
        return score
    
    def _analyze_color_variance(self, frame):
        """
        Color variance analysis for screen detection.
        
        Args:
            frame: BGR image
        
        Returns:
            float: Color score (0-1)
        """
        
        # Split channels
        b, g, r = cv2.split(frame)
        
        # Calculate variance in each channel
        var_b = np.var(b)
        var_g = np.var(g)
        var_r = np.var(r)
        
        total_variance = var_b + var_g + var_r
        
        # Calculate inter-channel differences
        bg_diff = np.mean(np.abs(b.astype(float) - g.astype(float)))
        gr_diff = np.mean(np.abs(g.astype(float) - r.astype(float)))
        rb_diff = np.mean(np.abs(r.astype(float) - b.astype(float)))
        
        channel_diversity = (bg_diff + gr_diff + rb_diff) / 3
        
        # Normalize variance score
        if total_variance >= config.COLOR_VARIANCE_OPTIMAL:
            variance_score = 1.0
        elif total_variance >= config.COLOR_VARIANCE_MIN:
            variance_score = 0.5 + 0.5 * (total_variance - config.COLOR_VARIANCE_MIN) / \
                           (config.COLOR_VARIANCE_OPTIMAL - config.COLOR_VARIANCE_MIN)
        else:
            variance_score = (total_variance / config.COLOR_VARIANCE_MIN) * 0.5
        
        # Normalize diversity score
        if channel_diversity >= config.CHANNEL_DIVERSITY_OPTIMAL:
            diversity_score = 1.0
        elif channel_diversity >= config.CHANNEL_DIVERSITY_MIN:
            diversity_score = 0.5 + 0.5 * (channel_diversity - config.CHANNEL_DIVERSITY_MIN) / \
                            (config.CHANNEL_DIVERSITY_OPTIMAL - config.CHANNEL_DIVERSITY_MIN)
        else:
            diversity_score = (channel_diversity / config.CHANNEL_DIVERSITY_MIN) * 0.5
        
        # Combine scores
        color_score = (variance_score * 0.6 + diversity_score * 0.4)
        
        return min(1.0, max(0.0, color_score))
    
    def _detect_patterns(self, gray):
        """
        Pattern detection using FFT.
        Detects regular patterns in prints/screens.
        
        Args:
            gray: Grayscale image
        
        Returns:
            float: Pattern score (0-1), higher = no patterns (good)
        """
        
        # Resize for faster FFT
        small = cv2.resize(gray, (config.FFT_SIZE, config.FFT_SIZE))
        
        # Apply FFT
        f = np.fft.fft2(small)
        fshift = np.fft.fftshift(f)
        magnitude = np.abs(fshift)
        
        # Remove DC component
        h, w = magnitude.shape
        r = config.FFT_DC_REMOVAL
        magnitude[h//2-r:h//2+r, w//2-r:w//2+r] = 0
        
        # Analyze frequency spectrum
        max_magnitude = np.max(magnitude)
        mean_magnitude = np.mean(magnitude)
        
        # Ratio indicates regular patterns
        ratio = max_magnitude / (mean_magnitude + 1)
        
        # High ratio = regular patterns = low score
        # Low ratio = irregular (natural) = high score
        if ratio >= config.FFT_PATTERN_THRESHOLD:
            score = 0.2  # Patterns detected
        else:
            score = 1.0 - (ratio / config.FFT_PATTERN_THRESHOLD) * 0.8
        
        return min(1.0, max(0.0, score))
    
    # ==========================================
    # SCORING AND RESULTS
    # ==========================================
    
    def _calculate_overall_score(self):
        """
        Calculate overall liveness score using weighted average.
        
        Returns:
            float: Overall score (0-1)
        """
        
        overall = 0.0
        
        for method, weight in config.WEIGHTS.items():
            overall += self.scores[method] * weight
        
        return min(1.0, max(0.0, overall))
    
    def _get_dynamic_instruction(self, overall_score, motion_score):
        """
        Generate dynamic instruction based on current scores.
        
        Args:
            overall_score: Overall liveness score
            motion_score: Motion detection score
        
        Returns:
            str: Instruction message
        """
        
        # Check motion level
        avg_motion = np.mean(list(self.motion_history)) if self.motion_history else 0
        
        if avg_motion < config.MOTION_THRESHOLD_MIN * 0.3:
            return config.INSTRUCTIONS['low_motion']
        elif avg_motion > config.MOTION_THRESHOLD_OPTIMAL * 1.5:
            return config.INSTRUCTIONS['too_much_motion']
        elif motion_score >= 0.6:
            return config.INSTRUCTIONS['good_motion']
        else:
            # Show progress
            progress_pct = int(overall_score * 100)
            return f"{config.INSTRUCTIONS['analyzing']} {progress_pct}%"
    
    def _create_result(self, status, progress, instruction, overall_score=0.0, attack_type=None):
        """
        Create result dictionary.
        
        Returns:
            dict: Complete analysis result
        """
        
        return {
            'status': status,
            'progress': progress,
            'confidence': self.confidence,
            'overall_score': overall_score,
            'scores': self.scores.copy(),
            'instruction': instruction,
            'attack_type': attack_type,
            'is_live': self.is_live,
            'frames_analyzed': self.frames_analyzed
        }
    
    def _print_scores(self, overall_score):
        """Print current scores to console."""
        print(f"\n[Frame {self.frames_analyzed}] Overall: {overall_score:.2f}")
        for method, score in self.scores.items():
            print(f"  {method}: {score:.2f}")
    
    def _get_attack_type(self):
        """Get primary attack type if SPOOF."""
        if self.is_live:
            return None
        
        primary_attack, _ = self.attack_detector.get_primary_attack()
        return primary_attack
    
    def _comprehensive_screen_check(self, frame, color_score):
        """
        Comprehensive screen detection using multiple methods.
        
        Args:
            frame: BGR image
            color_score: Color variance score
        
        Returns:
            bool: True if screen detected
        """
        
        screen_indicators = 0
        total_checks = 5
        
        # Check 1: Low color variance
        if color_score < config.SCREEN_VETO_THRESHOLD:
            screen_indicators += 1
            print(f"  Screen indicator 1: Low color variance ({color_score:.2f})")
        
        # Check 2: Brightness uniformity
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness_std = np.std(gray)
        if brightness_std < config.SCREEN_BRIGHTNESS_UNIFORMITY:
            screen_indicators += 1
            print(f"  Screen indicator 2: Uniform brightness (std={brightness_std:.1f})")
        
        # Check 3: RGB channel correlation (screens have high correlation)
        b, g, r = cv2.split(frame)
        corr_rg = np.corrcoef(r.flatten(), g.flatten())[0, 1]
        corr_gb = np.corrcoef(g.flatten(), b.flatten())[0, 1]
        avg_corr = (corr_rg + corr_gb) / 2
        
        if avg_corr > config.SCREEN_RGB_CORRELATION:
            screen_indicators += 1
            print(f"  Screen indicator 3: High RGB correlation ({avg_corr:.2f})")
        
        # Check 4: Edge sharpness (screens have very sharp edges)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        if edge_density < 0.05 or edge_density > 0.25:  # Too few or too many sharp edges
            screen_indicators += 1
            print(f"  Screen indicator 4: Abnormal edge density ({edge_density:.3f})")
        
        # Check 5: Screen reflection/glare detection
        # Screens often have bright spots (glare)
        bright_pixels = np.sum(gray > 240)
        bright_ratio = bright_pixels / gray.size
        if bright_ratio > 0.02:  # More than 2% very bright pixels
            screen_indicators += 1
            print(f"  Screen indicator 5: Glare detected ({bright_ratio:.3f})")
        
        # Decision: If 3 or more indicators, it's a screen
        is_screen = screen_indicators >= 3
        
        print(f"  Screen indicators: {screen_indicators}/{total_checks}")
        
        return is_screen


if __name__ == '__main__':
    """Test liveness detector."""
    print("="*70)
    print("Liveness Detector Module - Test Mode")
    print("="*70)
    
    detector = LivenessDetector()
    
    print("\nDetection Methods:")
    for method in detector.scores.keys():
        print(f"  • {method.replace('_', ' ').title()}")
    
    print(f"\nWeights: {config.WEIGHTS}")
    print(f"Threshold: {config.LIVENESS_THRESHOLD*100:.0f}%")
    
    print("\nModule ready!")