import pynput
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController, Key
import ctypes

class InputController:
    def __init__(self):
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.screen_width = ctypes.windll.user32.GetSystemMetrics(0)
        self.screen_height = ctypes.windll.user32.GetSystemMetrics(1)
        self.last_click_time = 0
        self.key_ctrl = Key.ctrl
        
    def move_cursor(self, x, y):
        """
        Moves the cursor to the specified coordinates (x, y).
        Uses ctypes SetCursorPos for lowest latency on Windows.
        """
        # Ensure coordinates are within screen bounds
        x = max(0, min(x, self.screen_width))
        y = max(0, min(y, self.screen_height))
        
        # pynput is sometimes slow/laggy for high freq updates
        # ctypes.windll.user32.SetCursorPos(int(x), int(y))
        
        # Reverting to pynput for safety/compatibility unless latency is issue
        # self.mouse.position = (x, y)
        ctypes.windll.user32.SetCursorPos(int(x), int(y))

    def click(self, button):
        current_time = 0 # Placeholder if we needed time-based buffering
        if button == 'left':
            self.mouse.click(Button.left, 1)
        elif button == 'right':
            self.mouse.click(Button.right, 1)

    def press_key(self, key_name):
        try:
            if hasattr(Key, key_name):
                key = getattr(Key, key_name)
            else:
                key = key_name
            self.keyboard.press(key)
            self.keyboard.release(key)
        except Exception as e:
            print(f"Error pressing key {key_name}: {e}")

    def scroll(self, dx=0, dy=0):
        """
        Scrolls the mouse wheel.
        dy > 0: Scroll Up
        dy < 0: Scroll Down
        """
        try:
            self.mouse.scroll(dx, dy)
        except Exception as e:
            print(f"Error scrolling: {e}")

    def get_active_window_title(self):
        """
        Returns the title of the currently active (foreground) window.
        """
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value

    def navigate_back(self):
        # Alt + Left Arrow
        with self.keyboard.pressed(Key.alt):
            self.keyboard.press(Key.left)
            self.keyboard.release(Key.left)

    def navigate_forward(self):
        # Alt + Right Arrow
        with self.keyboard.pressed(Key.alt):
            self.keyboard.press(Key.right)
            self.keyboard.release(Key.right)

    def prev_slide(self):
        # Left Arrow
        self.keyboard.press(Key.left)
        self.keyboard.release(Key.left)

    def next_slide(self):
        # Right Arrow
        self.keyboard.press(Key.right)
        self.keyboard.release(Key.right)
        
    def zoom(self, direction):
        # direction: 1 for in, -1 for out
        with self.keyboard.pressed(Key.ctrl):
            self.scroll(0, direction)
