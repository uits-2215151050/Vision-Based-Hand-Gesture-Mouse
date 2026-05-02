import cv2
import os
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import mediapipe as mp
from mediapipe.tasks.python.vision import hand_landmarker
from mediapipe.tasks.python import vision

# Config
DATASET_DIR = "dataset"
MODEL_PATH = "training/gesture_rf_model.joblib"

def extract_landmarks_from_image(image_path, landmarker):
    """
    Extracts 21 landmarks (x, y) flattened to 42 features.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
    
    try:
        detection_result = landmarker.detect(mp_image)
        if detection_result.hand_landmarks:
            # Take first hand
            marks = detection_result.hand_landmarks[0]
            # Normalize to 0-1 relative to image size?
            # MediaPipe outputs normalized coordinates (0-1) already.
            # Flatten
            features = []
            for m in marks:
                features.append(m.x)
                features.append(m.y)
                # features.append(m.z) # Z is not always reliable from single image but useful
            return features
    except Exception as e:
        # print(f"Error processing {image_path}: {e}")
        pass
    return None

def train():
    print(f"Python version is too new for TensorFlow. Using Random Forest on Landmarks.")
    
    if not os.path.exists(DATASET_DIR):
        print("Dataset directory not found.")
        return

    # Init MediaPipe for static images
    base_options = mp.tasks.BaseOptions(model_asset_path="hand_landmarker.task")
    options = hand_landmarker.HandLandmarkerOptions(
        base_options=base_options,
        num_hands=1,
        running_mode=vision.RunningMode.IMAGE)
    landmarker = hand_landmarker.HandLandmarker.create_from_options(options)

    X = []
    y = []
    
    classes = sorted(os.listdir(DATASET_DIR))
    print(f"Classes found: {classes}")
    
    for label in classes:
        label_dir = os.path.join(DATASET_DIR, label)
        if not os.path.isdir(label_dir):
            continue
            
        print(f"Processing {label}...")
        
        # Iterate all sequences/frames
        # Structure: dataset/Label/seq_00/00.jpg
        # Or dataset/Label/00.jpg depending on collector?
        # Collector creates seq_xx folders.
        
        for root, dirs, files in os.walk(label_dir):
            for file in files:
                if file.endswith(".jpg") or file.endswith(".png"):
                    path = os.path.join(root, file)
                    features = extract_landmarks_from_image(path, landmarker)
                    if features:
                        X.append(features)
                        y.append(label)

    X = np.array(X)
    y = np.array(y)
    
    if len(X) == 0:
        print("No landmarks extracted! Are the images cropped too tightly?")
        return
        
    print(f"\nTraining on {len(X)} samples.")
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train RF
    clf = RandomForestClassifier(n_estimators=100, max_depth=15, n_jobs=-1)
    clf.fit(X_train, y_train)
    
    # Eval
    probs = clf.predict_proba(X_test)
    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Model Accuracy: {acc*100:.2f}%")
    
    # Save
    joblib.dump(clf, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train()
