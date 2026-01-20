"""
TRACK D - MAIN DEMO APPLICATION
Comprehensive Liveness Detection System

Detects ALL spoofing attacks:
- Photo attack (printed fingerprint)
- Screen attack (phone/tablet display)
- Video replay attack  
- Fake finger (silicone/rubber replica)

Real-time continuous feedback with detailed scores!

Controls:
- Press 'Q' to quit
- Press 'R' to reset analysis
- Press 'S' to save result (when LIVE detected)
- Press 'D' to toggle debug mode
"""

import cv2
import os
from datetime import datetime
import config
from liveness_detector import LivenessDetector
from ui_helper import UIHelper
from finger_detector import FingerDetector


def main():
    """Main demo application."""
    
    print("="*70)
    print("        TRACK D: LIVENESS DETECTION SYSTEM")
    print("                 MAIN DEMO")
    print("="*70)
    
    # Validate configuration
    print("\nValidating configuration...")
    config.validate_config()
    
    # Initialize components
    print("\nInitializing components...")
    liveness_detector = LivenessDetector()
    ui_helper = UIHelper()
    finger_detector = FingerDetector()  # NEW: Finger detection
    
    # Create output directory
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    print(f"Output directory: {config.OUTPUT_DIR}/")
    
    # Open webcam
    print("\nOpening webcam...")
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("ERROR: Could not open webcam!")
        print("Please check:")
        print("  1. Camera is connected")
        print("  2. No other app is using camera")
        print("  3. Camera permissions are granted")
        return
    
    # Set resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.WINDOW_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.WINDOW_HEIGHT)
    
    print("✓ Webcam opened successfully!")
    
    print("\n" + "="*70)
    print("DEMO STARTED")
    print("="*70)
    print("\nOption B Flow:")
    print("  1. Show your index finger to camera")
    print("  2. Analysis starts automatically (5 seconds)")
    print("  3. Result shows: LIVE or SPOOF")
    print("  4. Press SPACE BAR to restart")
    print("\nControls:")
    print("  SPACE / R - Restart analysis")
    print("  S - Save result (when LIVE)")
    print("  Q - Quit")
    print("="*70 + "\n")
    
    # Create window
    window_name = 'Track D - Liveness Detection'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    # Counters
    frame_count = 0
    saved_count = 0
    
    # Analysis state
    analyzing = False
    
    print("Processing frames... (window should appear)\n")
    
    while True:
        # Read frame
        ret, frame = cap.read()
        
        if not ret:
            print("Failed to read frame!")
            break
        
        frame_count += 1
        
        # Detect finger
        finger_detected = finger_detector.is_finger_visible(frame)
        
        # Analyze frame (with finger detection status)
        result = liveness_detector.analyze_frame(frame, finger_detected)
        
        # Draw UI
        display_frame = ui_helper.draw_main_ui(frame, result)
        
        # Show frame
        cv2.imshow(window_name, display_frame)
        
        # Handle keys
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q') or key == ord('Q'):
            # Quit
            print("\n[QUIT] Closing demo...")
            break
        
        elif key == ord('r') or key == ord('R') or key == ord(' '):
            # Reset - SPACE BAR or R
            print("\n[RESTART] Resetting for new analysis...")
            liveness_detector.reset()
        
        elif key == ord('s') or key == ord('S'):
            # Save result
            if result['is_live'] and result['status'] == 'LIVE':
                filename = save_result(display_frame, result, saved_count)
                if filename:
                    saved_count += 1
                    print(f"\n[SAVED] {filename}")
                    print(f"  Overall Score: {result['overall_score']:.2f}")
                    print(f"  Confidence: {result['confidence']:.2f}")
            else:
                print("\n[ERROR] Cannot save - Not LIVE")
                if result['attack_type']:
                    print(f"  Attack detected: {result['attack_type']}")
        
        elif key == ord('d') or key == ord('D'):
            # Toggle debug
            config.DEBUG_MODE = not config.DEBUG_MODE
            config.PRINT_SCORES = config.DEBUG_MODE
            print(f"\n[DEBUG] Debug mode: {'ON' if config.DEBUG_MODE else 'OFF'}")
        
        # Print status periodically
        if frame_count % 30 == 0 and config.PRINT_SCORES:
            print(f"\n[Frame {frame_count}]")
            print(f"  Status: {result['status']}")
            print(f"  Progress: {result['progress']:.1f}%")
            print(f"  Overall: {result['overall_score']:.2f}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print("\n" + "="*70)
    print("DEMO ENDED")
    print("="*70)
    print(f"\nStatistics:")
    print(f"  Total frames processed: {frame_count}")
    print(f"  Results saved: {saved_count}")
    print(f"  Output directory: {config.OUTPUT_DIR}/")
    print("="*70 + "\n")


def save_result(frame, result, count):
    """
    Save detection result.
    
    Args:
        frame: Annotated frame
        result: Detection result dictionary
        count: Save counter
    
    Returns:
        str: Filename if saved, None otherwise
    """
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save image
        image_filename = f"{config.OUTPUT_DIR}/trackd_{timestamp}_{count}.{config.SAVE_IMAGE_FORMAT}"
        cv2.imwrite(image_filename, frame)
        
        # Save metadata
        metadata_filename = f"{config.OUTPUT_DIR}/trackd_{timestamp}_{count}.{config.SAVE_METADATA_FORMAT}"
        
        with open(metadata_filename, 'w') as f:
            f.write("="*60 + "\n")
            f.write("TRACK D - LIVENESS DETECTION RESULT\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Save Number: {count}\n\n")
            
            f.write("="*60 + "\n")
            f.write("OVERALL RESULT\n")
            f.write("="*60 + "\n")
            f.write(f"Status: {result['status']}\n")
            f.write(f"Is Live: {result['is_live']}\n")
            f.write(f"Overall Score: {result['overall_score']:.4f} ({int(result['overall_score']*100)}%)\n")
            f.write(f"Confidence: {result['confidence']:.4f} ({int(result['confidence']*100)}%)\n")
            f.write(f"Frames Analyzed: {result['frames_analyzed']}\n")
            
            if result['attack_type']:
                f.write(f"\nAttack Detected: {result['attack_type']}\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("DETAILED SCORES\n")
            f.write("="*60 + "\n")
            
            for method, score in result['scores'].items():
                weight = config.WEIGHTS[method]
                f.write(f"{method.replace('_', ' ').title():<25} {score:.4f} ({int(score*100):>3}%)  [Weight: {weight:.0%}]\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("DETECTION METHODS\n")
            f.write("="*60 + "\n")
            f.write("1. Motion Detection - Natural hand tremor analysis\n")
            f.write("2. Texture Analysis - Print/screen pattern detection\n")
            f.write("3. Consistency Check - Video replay detection\n")
            f.write("4. Edge Density - Fake finger detection\n")
            f.write("5. Color Variance - Screen backlight detection\n")
            f.write("6. Pattern Detection - FFT-based regular pattern detection\n")
            
            f.write("\n" + "="*60 + "\n")
            f.write("INTERPRETATION\n")
            f.write("="*60 + "\n")
            
            if result['is_live']:
                f.write("✓ LIVE FINGER DETECTED\n")
                f.write("This appears to be a real, live human finger.\n")
                f.write("All detection methods indicate genuine liveness.\n")
            else:
                f.write("✗ SPOOF DETECTED\n")
                f.write("This appears to be a spoofing attempt.\n")
                if result['attack_type']:
                    f.write(f"Primary attack type: {result['attack_type'].replace('_', ' ').title()}\n")
                f.write("One or more detection methods flagged suspicious patterns.\n")
            
            f.write("\n" + "="*60 + "\n")
        
        return image_filename
    
    except Exception as e:
        print(f"\n[ERROR] Failed to save: {e}")
        return None


if __name__ == '__main__':
    """Run main demo."""
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Demo stopped by user")
    except Exception as e:
        print(f"\n\n[ERROR] Demo crashed: {e}")
        import traceback
        traceback.print_exc()