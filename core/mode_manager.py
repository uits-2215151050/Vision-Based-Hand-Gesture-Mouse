import time
import cv2
import numpy as np
import math
from utils.calibration_manager import CalibrationManager
from core.gesture_engine import GestureEngine 

class Mode:
    def __init__(self, name):
        self.name = name
    
    def process(self, frame, analysis, input_ctrl, screen_dims, smoothed_pos, nn_gesture=None):
        pass

class NavigationMode(Mode):
    def __init__(self, calibration_mgr):
        super().__init__("Navigation")
        self.cal_mgr = calibration_mgr
        self.last_click_time = 0
        self.freeze_cursor = False
        self.scroll_mode = False
        self.left_pinch_active = False
        self.last_gesture_time = 0
        
    def process(self, frame, analysis, input_ctrl, screen_dims, smoothed_pos, nn_gesture=None):
        d = analysis["distances"]
        fingers = analysis.get("fingers_up", [False]*5) # [Thumb, Index, Middle, Ring, Pinky]
        palm = analysis["palm_pos"]
        middle_tip = analysis.get("middle_tip", (0,0))
        thumb_tip = analysis.get("thumb_tip", (0,0))
        
        h, w = frame.shape[:2]
        screen_w, screen_h = screen_dims
        current_time = time.time()

        # ---------------------------------------------------------
        # 1. HEURISTIC GESTURE LOGIC
        # ---------------------------------------------------------
        
        # Count non-thumb fingers up: Index, Middle, Ring, Pinky
        # fingers = [Thumb, Index, Middle, Ring, Pinky]
        
        up_count = sum([1 for i in range(1, 5) if fingers[i]])
        
        # --- SCROLL UP (3 Fingers: Index, Middle, Ring) ---
        if fingers[1] and fingers[2] and fingers[3] and not fingers[4]:
            self.freeze_cursor = True
            input_ctrl.scroll(0, 1) # Scroll Up
            cv2.putText(frame, "SCROLL UP", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 0), 2)
            
        # --- SCROLL DOWN (2 Fingers: Index, Middle) ---
        elif fingers[1] and fingers[2] and not fingers[3] and not fingers[4]:
            self.freeze_cursor = True
            input_ctrl.scroll(0, -1) # Scroll Down # Wait, user said "two finger up for scroll down"
            cv2.putText(frame, "SCROLL DOWN", (30, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 0), 2)

        # --- NAV (Thumb Stick: All fingers closed except Thumb?) ---
        # Actually user said "rest of the thing is as usual".
        # Usual Nav was "Fist with Thumb extended".
        elif fingers[0] and up_count == 0: 
            self.freeze_cursor = True
             # Check Direction relative to Palm Check
            margin = w * 0.05
            if thumb_tip[0] < palm[0] - margin: # Left
                 if current_time - self.last_gesture_time > 0.5:
                    title = input_ctrl.get_active_window_title().lower()
                    presentation_apps = ["powerpoint", "slide", "canva", "presentation"]
                    if any(app in title for app in presentation_apps):
                        input_ctrl.prev_slide()
                        cv2.putText(frame, "PREV SLIDE", (w//2, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                    else:
                        input_ctrl.navigate_back()
                        cv2.putText(frame, "BACK", (w//2, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                    self.last_gesture_time = current_time
                    
            elif thumb_tip[0] > palm[0] + margin: # Right
                 if current_time - self.last_gesture_time > 0.5:
                    title = input_ctrl.get_active_window_title().lower()
                    presentation_apps = ["powerpoint", "slide", "canva", "presentation"]
                    if any(app in title for app in presentation_apps):
                        input_ctrl.next_slide()
                        cv2.putText(frame, "NEXT SLIDE", (w//2, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    else:
                        input_ctrl.navigate_forward()
                        cv2.putText(frame, "FORWARD", (w//2, h//2), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
                    self.last_gesture_time = current_time
        
        else:
            # --- CURSOR & CLICK ---
            # User said "Five finger up for cursor movement".
            # Also "Rest is usual" -> Click is Pinch.
            
            unit = w * 0.08  
            pinch_thresh = unit * 0.45 
            is_pinched_index = d["thumb_index"] < pinch_thresh
            
            # Click overrides everything
            if is_pinched_index:
                if not self.left_pinch_active:
                    input_ctrl.click('left')
                    self.left_pinch_active = True
                    cv2.putText(frame, "LEFT CLICK", (30, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Allow drag while pinching
                self.freeze_cursor = False 
                
            else:
                self.left_pinch_active = False
                
                # Cursor Movement Condition: 5 Fingers Up (Open Palm)
                # fingers = [Thumb, Index, Middle, Ring, Pinky]
                # "5 fingers" = all(fingers)
                if all(fingers):
                    self.freeze_cursor = False
                else:
                    # If not 5 fingers and not pinch and not scroll/nav -> Freeze
                    self.freeze_cursor = True
            
            # Move if not frozen
            if not self.freeze_cursor:
                # Mapping Logic
                bounds = self.cal_mgr.get_bounds()
                valid_calibration = False
                if bounds:
                    if bounds["max_x"] <= w and bounds["max_y"] <= h:
                        valid_calibration = True

                if valid_calibration:
                    min_x, max_x = bounds["min_x"], bounds["max_x"]
                    min_y, max_y = bounds["min_y"], bounds["max_y"]
                    cv2.rectangle(frame, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (0, 255, 255), 2)
                else:
                    margin_x = int(w * 0.15)
                    margin_y = int(h * 0.15)
                    min_x, max_x = margin_x, w - margin_x
                    min_y, max_y = margin_y, h - margin_y
                    cv2.rectangle(frame, (margin_x, margin_y), (w - margin_x, h - margin_y), (255, 0, 255), 2)

                clamped_x = np.clip(smoothed_pos[0], min_x, max_x)
                clamped_y = np.clip(smoothed_pos[1], min_y, max_y)
                screen_x = np.interp(clamped_x, (min_x, max_x), (0, screen_w))
                screen_y = np.interp(clamped_y, (min_y, max_y), (0, screen_h))
                
                input_ctrl.move_cursor(screen_x, screen_y)

class CalibrationMode(Mode):
    def __init__(self, calibration_mgr):
        super().__init__("Calibration")
        self.cal_mgr = calibration_mgr
        self.last_record_time = 0
        
    def process(self, frame, analysis, input_ctrl, screen_dims, smoothed_pos, nn_gesture=None):
        h, w = frame.shape[:2]
        idx = self.cal_mgr.active_corner_index
        unit = w * 0.08
        pinch_thresh = unit * 0.45
        
        msgs = [
            "Touch Top-Left Corner",
            "Touch Top-Right Corner",
            "Touch Bottom-Right Corner",
            "Touch Bottom-Left Corner",
            "Calibration Done!"
        ]
        
        if idx < 4:
            msg = msgs[idx]
        else:
            msg = msgs[4]
            cv2.putText(frame, "Saved! Switch to Navigation", (50, h//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            return
            
        cv2.putText(frame, f"CALIBRATION: {msg}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, "Pinch to Record Point", (30, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        targets = [(100, 100), (w-100, 100), (w-100, h-100), (100, h-100)]
        target = targets[idx]
        cv2.circle(frame, target, 15, (0, 255, 255), 2)
        
        d = analysis["distances"]
        if d["thumb_index"] < pinch_thresh:
            current_time = time.time()
            if current_time - self.last_record_time > 1.5: 
                success = self.cal_mgr.record_point(smoothed_pos)
                self.last_record_time = current_time
                cv2.putText(frame, "RECORDED!", (target[0], target[1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

class ModeManager:
    def __init__(self):
        self.cal_mgr = CalibrationManager()
        self.modes = {
            "Navigation": NavigationMode(self.cal_mgr),
            "Calibration": CalibrationMode(self.cal_mgr)
        }
        self.current_mode_name = "Navigation"
    
    def get_active_mode(self):
        return self.modes[self.current_mode_name]
    
    def switch_mode(self, mode_name):
        if mode_name in self.modes:
            if mode_name == "Calibration":
                self.cal_mgr.start_calibration()
            self.current_mode_name = mode_name
            return True
        return False
