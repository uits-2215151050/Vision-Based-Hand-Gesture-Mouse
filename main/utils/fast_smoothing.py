import math
import time

class OneEuroFilter:
    def __init__(self, min_cutoff=1.0, beta=0.0):
        self.freq = 30.0
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.x_filter = LowPassFilter()
        self.y_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.dy_filter = LowPassFilter()
        self.last_timestamp = None

    def __call__(self, x, y, timestamp=None):
        # timestamp in seconds
        if timestamp is None:
            timestamp = time.time()
            
        if self.last_timestamp is None:
             self.last_timestamp = timestamp
             self.x_filter.set_alpha(1.0)
             self.y_filter.set_alpha(1.0)
             return self.x_filter(x), self.y_filter(y)

        dt = timestamp - self.last_timestamp
        self.last_timestamp = timestamp
        
        # Avoid divide by zero
        if dt <= 0: dt = 0.00001
        
        self.freq = 1.0 / dt
        
        # Estimate derivative (speed)
        dx = (x - self.x_filter.last_val) * self.freq
        dy = (y - self.y_filter.last_val) * self.freq
        
        # Smooth the derivative
        dx_smoothed = self.dx_filter(dx, self.alpha(1.0)) # 1hz cutoff for derivative
        dy_smoothed = self.dy_filter(dy, self.alpha(1.0))
        
        # Calculate dynamic cutoff
        cutoff = self.min_cutoff + self.beta * math.sqrt(dx_smoothed**2 + dy_smoothed**2)
        
        # Filter the signal
        return self.x_filter(x, self.alpha(cutoff)), self.y_filter(y, self.alpha(cutoff))

    def alpha(self, cutoff):
        tau = 1.0 / (2 * math.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)

class LowPassFilter:
    def __init__(self):
        self.last_val = 0.0
        self.alpha_val = 1.0 # 1.0 means no smoothing
        self.initialized = False

    def set_alpha(self, alpha):
        self.alpha_val = alpha

    def __call__(self, val, alpha=None):
        if alpha is not None:
            self.alpha_val = alpha
            
        if not self.initialized:
            self.last_val = val
            self.initialized = True
            return val
            
        self.last_val = self.alpha_val * val + (1.0 - self.alpha_val) * self.last_val
        return self.last_val
