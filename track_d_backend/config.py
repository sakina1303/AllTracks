"""
Configuration File for Track D - Liveness Detection
All parameters and thresholds in one place
"""

# ========================================
# MOTION DETECTION PARAMETERS
# ========================================

# Number of frames to analyze for motion
MOTION_FRAMES = 10

# Motion thresholds (pixels changed per frame)
MOTION_THRESHOLD_MIN = 500      # Minimum for partial credit
MOTION_THRESHOLD_OPTIMAL = 2000 # Optimal motion detected

# Motion detection sensitivity
MOTION_PIXEL_THRESHOLD = 15     # Grayscale difference to count as motion


# ========================================
# TEXTURE ANALYSIS PARAMETERS
# ========================================

# Texture variance thresholds
TEXTURE_VARIANCE_MIN = 80       # Minimum variance for real skin
TEXTURE_VARIANCE_OPTIMAL = 150  # Optimal variance

# High-frequency content threshold
HF_CONTENT_MIN = 150            # Minimum edge energy
HF_CONTENT_OPTIMAL = 300        # Optimal edge energy

# Local Binary Pattern threshold
LBP_DIVERSITY_MIN = 25          # Minimum gradient diversity


# ========================================
# CONSISTENCY CHECK PARAMETERS
# ========================================

# Brightness consistency
CONSISTENCY_THRESHOLD = 15      # Max average brightness change
FRAME_JUMP_THRESHOLD = 40       # Max single-frame jump (video loop)

# Temporal consistency window
CONSISTENCY_WINDOW = 5          # Frames to check


# ========================================
# EDGE DENSITY PARAMETERS (Fake Finger)
# ========================================

# Edge density range for real skin
EDGE_DENSITY_MIN = 0.15
EDGE_DENSITY_MAX = 0.35

# Canny edge detection parameters
CANNY_THRESHOLD_LOW = 50
CANNY_THRESHOLD_HIGH = 150


# ========================================
# COLOR VARIANCE PARAMETERS (Screen Detection)
# ========================================

# Color channel variance thresholds
COLOR_VARIANCE_MIN = 200        # Minimum total RGB variance
COLOR_VARIANCE_OPTIMAL = 500    # Optimal variance

# Inter-channel diversity
CHANNEL_DIVERSITY_MIN = 5       # Minimum between channels
CHANNEL_DIVERSITY_OPTIMAL = 20  # Optimal diversity


# ========================================
# PATTERN DETECTION (Print/Screen)
# ========================================

# FFT-based pattern detection
FFT_SIZE = 128                  # FFT computation size
FFT_PATTERN_THRESHOLD = 50      # Regular pattern indicator
FFT_DC_REMOVAL = 5              # DC component removal radius


# ========================================
# OVERALL SCORING WEIGHTS (ANTI-SPOOF FOCUSED)
# ========================================

# Weight for each detection method (must sum to 1.0)
# Prioritize methods that catch spoofing attacks
WEIGHTS = {
    'motion': 0.30,              # 30% - Important but not only factor
    'texture': 0.20,             # 20% - Catches prints
    'consistency': 0.10,         # 10% - Catches video replay
    'edge_density': 0.10,        # 10% - Catches fake fingers
    'color_variance': 0.20,      # 20% - CRITICAL for screen detection
    'pattern_detection': 0.10    # 10% - Catches prints/screens
}


# ========================================
# DECISION THRESHOLDS
# ========================================

# Overall liveness score threshold (STRICTER)
LIVENESS_THRESHOLD = 0.70       # 70% minimum to pass (was 60%)

# Confidence levels
CONFIDENCE_HIGH = 0.85          # 85%+ = HIGH confidence
CONFIDENCE_MEDIUM = 0.70        # 70-85% = MEDIUM confidence
CONFIDENCE_LOW = 0.50           # 50-70% = LOW confidence
# Below 50% = SPOOF

# CRITICAL: Screen detection veto
# If screen detected with high confidence, automatic SPOOF
SCREEN_VETO_ENABLED = True
SCREEN_VETO_THRESHOLD = 0.50     # If color variance < 50%, likely screen (was 40%)

# Additional screen checks
SCREEN_BRIGHTNESS_UNIFORMITY = 15  # Screens have uniform brightness
SCREEN_RGB_CORRELATION = 0.85      # Screens have high RGB correlation


# ========================================
# ATTACK-SPECIFIC THRESHOLDS (STRICTER)
# ========================================

# Photo attack indicators (MORE STRICT)
PHOTO_ATTACK_MOTION_MAX = 200       # Very low motion (was 100)
PHOTO_ATTACK_TEXTURE_MAX = 0.5      # Low texture score (was 0.4)

# Screen attack indicators (MUCH STRICTER)
SCREEN_ATTACK_COLOR_VAR_MAX = 200   # Low color variance (was 150)
SCREEN_ATTACK_PATTERN_MIN = 0.4     # Regular patterns detected (was 0.5)
SCREEN_ATTACK_UNIFORMITY_MAX = 20   # Brightness uniformity

# Video replay indicators (MORE STRICT)
VIDEO_REPLAY_JUMP_MIN = 35          # Large brightness jumps (was 40)
VIDEO_REPLAY_REPEAT_THRESHOLD = 0.75 # Pattern repetition (was 0.8)

# Fake finger indicators (MORE STRICT)
FAKE_FINGER_EDGE_LOW = 0.12         # Very low edges (was 0.10)
FAKE_FINGER_EDGE_HIGH = 0.40        # Too many edges (was 0.45)


# ========================================
# ANALYSIS SETTINGS
# ========================================

# Minimum frames before making decision (REDUCED FOR SPEED)
MIN_FRAMES_FOR_DECISION = 15  # About 5 seconds at 3 FPS

# Maximum frames to analyze
MAX_FRAMES_TO_ANALYZE = 30

# Frame processing interval (process every Nth frame)
FRAME_SKIP = 1                  # Process every frame (1 = no skip)


# ========================================
# UI DISPLAY SETTINGS
# ========================================

# Window size
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600

# Professional color scheme (BGR format)
COLOR_LIVE = (100, 200, 100)        # Soft green
COLOR_SPOOF = (80, 80, 220)         # Soft red
COLOR_ANALYZING = (220, 180, 100)   # Soft blue
COLOR_WARNING = (60, 150, 255)      # Soft orange
COLOR_TEXT = (240, 240, 240)        # Off-white
COLOR_BACKGROUND = (40, 40, 40)     # Dark gray
COLOR_PANEL_BG = (50, 50, 50)       # Slightly lighter gray
COLOR_ACCENT = (200, 150, 80)       # Blue accent

# Font settings
FONT = 0  # cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE_LARGE = 1.2
FONT_SCALE_MEDIUM = 0.8
FONT_SCALE_SMALL = 0.6
FONT_THICKNESS_BOLD = 3
FONT_THICKNESS_NORMAL = 2
FONT_THICKNESS_THIN = 1

# UI Timing
ANALYSIS_DURATION = 5   # Seconds to analyze before final decision (FAST)
SHOW_TIMER = True       # Show countdown timer
FADE_TRANSITION = True  # Smooth fade transition


# ========================================
# SAVE SETTINGS
# ========================================

# Output directory
OUTPUT_DIR = 'trackd_results'

# Save format
SAVE_IMAGE_FORMAT = 'png'
SAVE_METADATA_FORMAT = 'txt'


# ========================================
# INSTRUCTION MESSAGES
# ========================================

INSTRUCTIONS = {
    'initial': "Show your finger to camera",
    'collecting': "Collecting frames...",
    'low_motion': "Please move your finger slightly",
    'too_much_motion': "Keep your finger more steady",
    'good_motion': "Good! Continue...",
    'analyzing': "Analyzing liveness...",
    'live_detected': "✓ LIVE FINGER DETECTED",
    'spoof_detected': "✗ SPOOF DETECTED",
    'photo_attack': "Photo/Print detected - Use real finger",
    'screen_attack': "Screen detected - Use real finger",
    'video_replay': "Video replay detected - Use real finger",
    'fake_finger': "Fake finger detected - Use real finger",
    'uncertain': "Unable to determine - Try again",
}


# ========================================
# DEBUG SETTINGS
# ========================================

# Enable debug output
DEBUG_MODE = False

# Show intermediate results
SHOW_DEBUG_INFO = False

# Print scores to console
PRINT_SCORES = True


# ========================================
# VALIDATION
# ========================================

def validate_config():
    """Validate configuration parameters."""
    
    # Check weights sum to 1.0
    total_weight = sum(WEIGHTS.values())
    if not (0.99 <= total_weight <= 1.01):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    # Check thresholds are in valid range
    if not (0 <= LIVENESS_THRESHOLD <= 1):
        raise ValueError("LIVENESS_THRESHOLD must be between 0 and 1")
    
    print("✓ Configuration validated successfully")
    return True


if __name__ == '__main__':
    """Test configuration."""
    print("="*70)
    print("Track D Configuration")
    print("="*70)
    
    print("\nMotion Detection:")
    print(f"  Frames: {MOTION_FRAMES}")
    print(f"  Threshold: {MOTION_THRESHOLD_MIN} - {MOTION_THRESHOLD_OPTIMAL}")
    
    print("\nWeights:")
    for key, value in WEIGHTS.items():
        print(f"  {key}: {value*100:.0f}%")
    
    print(f"\nLiveness Threshold: {LIVENESS_THRESHOLD*100:.0f}%")
    
    print("\nValidating...")
    validate_config()