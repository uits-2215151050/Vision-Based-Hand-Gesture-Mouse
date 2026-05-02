import cv2
import os
import time
import numpy as np
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.gesture_engine import GestureEngine

# Configuration
DATASET_DIR = "dataset"
IMG_SIZE = 128
FRAMES_PER_SEQUENCE = 16
PADDING = 40  # Pixel padding around the hand

def get_bbox_from_landmarks(landmarks, h, w):
    """
    Computes bounding box from landmarks with padding.
    """
    x_coords = [lm[0] for lm in landmarks]
    y_coords = [lm[1] for lm in landmarks]
    
    min_x = max(0, int(min(x_coords)) - PADDING)
    max_x = min(w, int(max(x_coords)) + PADDING)
    min_y = max(0, int(min(y_coords)) - PADDING)
    max_y = min(h, int(max(y_coords)) + PADDING)
    
    # Make it square if possible, or just rectangular?
    # CNN expects 128x128, so we usually just resize the crop.
    # But aspect ratio preservation is usually better.
    # For simplicity of this specific architecture, we'll just strict crop and resize.
    
    return min_x, min_y, max_x, max_y

def collect_data():
    engine = GestureEngine()
    cap = cv2.VideoCapture(0)
    
    print("\n=== Gesture Data Collector ===")
    label = input("Enter gesture label (e.g., SwipeLeft): ").strip()
    if not label:
        return

    save_dir = os.path.join(DATASET_DIR, label)
    os.makedirs(save_dir, exist_ok=True)
    
    # Count existing sequences to auto-increment ID
    existing_seqs = len([d for d in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, d))])
    seq_counter = existing_seqs
    
    print(f"\nCollecting data for '{label}'.")
    print("Press 'R' to record a sequence.")
    print("Press 'Q' to quit.")
    
    recording = False
    frame_count = 0
    current_seq_dir = ""
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        timestamp_ms = int(time.time() * 1000)
        
        # 1. Detect Hand
        result = engine.process_frame(frame, timestamp_ms)
        landmarks = engine.extract_landmarks(result, frame.shape)
        
        # Visualization
        display_frame = frame.copy()
        hand_crop = None
        
        if landmarks:
            # Draw landmarks
            for x, y in landmarks:
                cv2.circle(display_frame, (int(x), int(y)), 2, (0, 255, 0), -1)
            
            # Get Bounding Box
            h, w, _ = frame.shape
            x1, y1, x2, y2 = get_bbox_from_landmarks(landmarks, h, w)
            cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            
            # Crop Hand
            hand_crop = frame[y1:y2, x1:x2]
            if hand_crop.size > 0:
                hand_crop = cv2.resize(hand_crop, (IMG_SIZE, IMG_SIZE))
                
                # Show crop
                cv2.imshow("Hand Crop", hand_crop)
        
        # 2. Recording Logic
        if recording:
            if landmarks is None:
                print("No hand detected! Stopping recording.")
                recording = False
                frame_count = 0
                # Optionally delete the partial folder
                continue
                
            # Save frame
            frame_path = os.path.join(current_seq_dir, f"{frame_count:02d}.jpg")
            cv2.imwrite(frame_path, hand_crop)
            
            cv2.putText(display_frame, f"REC: {frame_count}/{FRAMES_PER_SEQUENCE}", (10, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            frame_count += 1
            if frame_count >= FRAMES_PER_SEQUENCE:
                print(f"Sequence {seq_counter} saved.")
                recording = False
                seq_counter += 1
                frame_count = 0
        else:
            cv2.putText(display_frame, f"Label: {label} | Seq: {seq_counter}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(display_frame, "Press 'R' to Record", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Data Collector", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('r') and not recording:
            print("Recording started...")
            recording = True
            frame_count = 0
            current_seq_dir = os.path.join(save_dir, f"seq_{seq_counter:03d}")
            os.makedirs(current_seq_dir, exist_ok=True)
            
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    collect_data()
