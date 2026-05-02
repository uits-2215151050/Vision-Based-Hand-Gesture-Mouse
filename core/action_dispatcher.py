from .mode_manager import ModeManager
import cv2

class ActionDispatcher:
    def __init__(self, input_ctrl):
        self.input_ctrl = input_ctrl
        self.mode_manager = ModeManager()
        
    def process(self, frame, analysis, engine_smoothed_pos, nn_gesture=None):
        """
        engine_smoothed_pos: tuple (x, y) - already smoothed coordinates
        analysis: raw analysis data (distances etc.)
        """
        if not analysis:
            return

        active_mode = self.mode_manager.get_active_mode()
        
        # We pass smoothed_pos separately
        
        screen_dims = (self.input_ctrl.screen_width, self.input_ctrl.screen_height)
        
        # Cleanup: Don't modify analysis object, just pass smoothed_pos
        active_mode.process(frame, analysis, self.input_ctrl, screen_dims, engine_smoothed_pos, nn_gesture)

    def set_mode(self, mode_name):
        self.mode_manager.switch_mode(mode_name)
    
    def get_mode_name(self):
        return self.mode_manager.current_mode_name
