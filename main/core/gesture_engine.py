import mediapipe as mp
from mediapipe.tasks.python.vision import hand_landmarker
from mediapipe.tasks.python import vision
import cv2
import time
import os
import urllib.request
from utils import util
from utils.fast_smoothing import OneEuroFilter
import numpy as np
import joblib

class GestureEngine:
    def __init__(self, model_path="hand_landmarker.task", rf_model_path="training/gesture_rf_model.joblib"):
        """
        Initializes the MediaPipe HandLandmarker and the Random Forest Model.
        """
        # 1. MediaPipe Setup
        self.model_path = model_path
        self._ensure_model_exists()
        
        base_options = mp.tasks.BaseOptions(model_asset_path=self.model_path)
        hl_options = hand_landmarker.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1,
            running_mode=vision.RunningMode.VIDEO,
        )
        self.landmarker = hand_landmarker.HandLandmarker.create_from_options(hl_options)
        
        # 2. Smoothing state
        # 2. Smoothing state
        # min_cutoff: 0.004 = very smooth/heavy. 
        # beta: 0.05 = less jitter, slightly more lag but better control.
        self.smoother = OneEuroFilter(min_cutoff=0.004, beta=0.05) 
        
        # 3. RF Model Setup
        self.rf_model = None
        # 3. RF Model Setup
        self.rf_model = None
        # DISABLED for Heuristic Mode
        # if os.path.exists(rf_model_path):
        #     try:
        #         print(f"Loading RF Model: {rf_model_path}...")
        #         self.rf_model = joblib.load(rf_model_path)
        #         print("RF Model loaded successfully.")
        #     except Exception as e:
        #         print(f"Failed to load RF model: {e}")
        # else:
        #     print("RF model not found. Run training/train_model.py.")
            
        self.prediction_cooldown = 0

    def _ensure_model_exists(self):
        if not os.path.exists(self.model_path):
            try:
                print("Downloading HandLandmarker model...")
                url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
                urllib.request.urlretrieve(url, self.model_path)
                print("Download complete.")
            except Exception as e:
                print(f"Failed to download model: {e}")

    def process_frame(self, frame, timestamp_ms):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        try:
            return self.landmarker.detect_for_video(mp_image, timestamp_ms)
        except Exception as e:
            print(f"Inference error: {e}")
            return None

    def predict_gesture_nn(self, frame, landmarks_px):
        """
        Actually predicts using Random Forest on Normalized Landmarks.
        We need the original result for normalized landmarks, but passed landmarks_px 
        is easier for API compatibility. 
        Wait, I need the normalized landmarks. 
        I'll assume I can access them via the `result` object if I store it, 
        or I can re-normalize landmarks_px (less accurate if crop changed).
        
        BETTER: Update `predict_gesture_nn` signature or 
        just accept that I need to pass the `result` object to this method?
        
        Actually, `main_window.py` calls:
        nn_gesture, confidence = self.engine.predict_gesture_nn(frame, landmarks_px)
        
        I should update the signature in `process_frame` or `extract_and_predict`?
        
        Let's change the signature of `predict_gesture_nn` to accept `result`.
        """
        # Placeholder compatible signature implementation:
        # We can't easily get normalized from pixel without frame size.
        # But `frame` is passed.
        
        # Actually I will change the caller in main_window to pass `result`.
        return None, 0.0

    def predict_gesture_from_result(self, result):
        if self.rf_model is None or not result or not result.hand_landmarks:
            return None, 0.0
            
        if self.prediction_cooldown > 0:
            self.prediction_cooldown -= 1
            return None, 0.0
            
        # Extract features (normalized x, y)
        marks = result.hand_landmarks[0]
        features = []
        for m in marks:
            features.append(m.x)
            features.append(m.y)
            
        # Predict
        try:
            features = np.array([features])
            prediction = self.rf_model.predict(features)[0]
            probs = self.rf_model.predict_proba(features)[0]
            confidence = np.max(probs)
            
            if confidence > 0.6: # Threshold
                self.prediction_cooldown = 5 # Small cooldown
                return prediction, float(confidence)
            else:
                 # Debug low confidence
                 if confidence > 0.3:
                     print(f"Low Conf: {prediction} ({confidence:.2f})")
        except Exception as e:
            print(f"Prediction Error: {e}")
            
        return None, 0.0

    def apply_smoothing(self, target_x, target_y, timestamp):
        return self.smoother(target_x, target_y, timestamp)

    def extract_landmarks(self, result, frame_shape):
        if not result or not result.hand_landmarks:
            return None
        h, w = frame_shape[:2]
        lm_list = result.hand_landmarks[0]
        return [(lm.x * w, lm.y * h) for lm in lm_list]
    
    def analyze_gesture(self, landmarks_px):
        if not landmarks_px: return None
        thumb_tip = landmarks_px[4]
        index_tip = landmarks_px[8]
        middle_tip = landmarks_px[12]
        ring_tip = landmarks_px[16]
        pinky_tip = landmarks_px[20]
        palm = landmarks_px[0]

        return {
            "palm_pos": palm,
            "middle_tip": middle_tip, # For orientation check
            "thumb_tip": thumb_tip, # For nav check
            "distances": {
                "thumb_index": util.get_distance(thumb_tip, index_tip),
                "thumb_middle": util.get_distance(thumb_tip, middle_tip),
                "index_middle": util.get_distance(index_tip, middle_tip),
                "thumb_ring": util.get_distance(thumb_tip, ring_tip),
                "thumb_pinky": util.get_distance(thumb_tip, pinky_tip)
            },
            "fingers_up": self._get_fingers_up(landmarks_px)
        }

    def _get_fingers_up(self, lm):
        # 0: Wrist
        # Tips: 4, 8, 12, 16, 20
        # PIPs: 2, 6, 10, 14, 18 (Using MCP or PIP for reference)
        # Check dist(Tip, Wrist) vs dist(PIP, Wrist)
        wrist = lm[0]
        fingers = []
        
        # Thumb: Compare Tip(4) vs IP(3) to Wrist ?? Thumb is tricky. 
        # Usually checking x offset for thumb relative to knuckle is better but for simple Open/Close:
        # tip(4) vs mcp(2) distance to wrist?
        # Let's use simple distance ratio or comparison
        
        # Thumb (4 vs 2)
        fingers.append(util.get_distance(lm[4], wrist) > util.get_distance(lm[3], wrist))
        
        # Others (Tip vs PIP - 6, 10, 14, 18)
        fingers.append(util.get_distance(lm[8], wrist) > util.get_distance(lm[6], wrist)) # Index
        fingers.append(util.get_distance(lm[12], wrist) > util.get_distance(lm[10], wrist)) # Middle
        fingers.append(util.get_distance(lm[16], wrist) > util.get_distance(lm[14], wrist)) # Ring
        fingers.append(util.get_distance(lm[20], wrist) > util.get_distance(lm[18], wrist)) # Pinky
        
        return fingers
