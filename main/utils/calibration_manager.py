import json
import os

class CalibrationManager:
    def __init__(self, filename="calibration.json"):
        self.filename = filename
        self.corners = [] # TL, TR, BR, BL
        self.active_corner_index = 0
        self.is_calibrating = False
        self.bounds = self.load_calibration()
    
    def start_calibration(self):
        self.corners = []
        self.active_corner_index = 0
        self.is_calibrating = True
        print("Calibration started.")

    def record_point(self, point):
        """
        Records the current palm position as a corner.
        point: (x, y)
        Returns: True if calibration is finished, False otherwise.
        """
        if not self.is_calibrating:
            return False
            
        print(f"Recorded corner {self.active_corner_index}: {point}")
        self.corners.append(point)
        self.active_corner_index += 1
        
        if(len(self.corners) >= 4):
            self._finalize_calibration()
            self.is_calibrating = False
            return True
            
        return False

    def _finalize_calibration(self):
        # Compute min/max from corners
        # This assumes fairly rectlinear alignment but is robust enough
        xs = [p[0] for p in self.corners]
        ys = [p[1] for p in self.corners]
        
        self.bounds = {
            "min_x": min(xs),
            "max_x": max(xs),
            "min_y": min(ys),
            "max_y": max(ys)
        }
        self.save_calibration()
        print(f"Calibration saved: {self.bounds}")

    def save_calibration(self):
        try:
            with open(self.filename, "w") as f:
                json.dump(self.bounds, f)
        except Exception as e:
            print(f"Error saving calibration: {e}")

    def load_calibration(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading calibration: {e}")
        
        # Default fallback (conservative ROI logic is moved here or just return None to let Mode handle defaults)
        return None
    
    def get_bounds(self):
         return self.bounds
