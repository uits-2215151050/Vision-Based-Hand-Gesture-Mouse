import cv2
import threading
import queue
import time
import numpy as np

class CameraThread:
    def __init__(self, frame_queue, stop_event):
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread_started = False

    def start(self):
        if not self.thread_started:
            self.thread.start()
            self.thread_started = True

    def _run(self):
        print("Camera Thread: Starting...")
        cap = cv2.VideoCapture(0)
        print("Camera Thread: VideoCapture(0) opened")
        
        # Low latency settings
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        while not self.stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break
                
            frame = cv2.flip(frame, 1) # Mirror effect
            
            # Put frame in queue (blocking if full to avoid lag buildup)
            try:
                # If queue is full, get rid of oldest frame
                if self.frame_queue.full():
                    try: self.frame_queue.get_nowait()
                    except queue.Empty: pass
                
                self.frame_queue.put(frame, timeout=1)
            except:
                pass
                
        cap.release()
        print("Camera Thread: Stopped")


class NetworkCamera:
    """Camera that receives frames from mobile device via camera server"""
    
    def __init__(self, frame_queue, stop_event, camera_server):
        self.frame_queue = frame_queue
        self.stop_event = stop_event
        self.camera_server = camera_server
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread_started = False
        self.frame_count = 0
        self.last_log_time = time.time()
    
    def start(self):
        if not self.thread_started:
            self.thread.start()
            self.thread_started = True
    
    def _run(self):
        print("[Network Camera] Starting...")
        print("[Network Camera] Waiting for frames from mobile device...")
        
        no_frame_count = 0
        
        while not self.stop_event.is_set():
            try:
                # Get latest frame from server
                frame_data = self.camera_server.get_latest_frame()
                
                if frame_data is not None:
                    # Reset no-frame counter
                    if no_frame_count > 0:
                        print(f"[Network Camera] Frame received after {no_frame_count} empty polls")
                        no_frame_count = 0
                    
                    # Decode JPEG to numpy array
                    nparr = np.frombuffer(frame_data, np.uint8)
                    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        self.frame_count += 1
                        
                        # Log every 30 frames
                        if self.frame_count % 30 == 0:
                            elapsed = time.time() - self.last_log_time
                            fps = 30 / elapsed if elapsed > 0 else 0
                            print(f"[Network Camera] Processed {self.frame_count} frames (Current FPS: {fps:.1f})")
                            self.last_log_time = time.time()
                        
                        # Mirror effect (optional, can be removed if mobile already mirrors)
                        frame = cv2.flip(frame, 1)
                        
                        # Put frame in queue
                        if self.frame_queue.full():
                            try: self.frame_queue.get_nowait()
                            except queue.Empty: pass
                        
                        self.frame_queue.put(frame, timeout=0.1)
                    else:
                        print("[Network Camera] ERROR: Failed to decode frame")
                else:
                    # No frame available
                    no_frame_count += 1
                    
                    # Log every 100 empty polls (roughly every 3 seconds)
                    if no_frame_count % 100 == 0:
                        print(f"[Network Camera] Waiting for frames... ({no_frame_count} polls)")
                    
                    time.sleep(0.033)  # ~30fps polling rate
                    
            except Exception as e:
                print(f"[Network Camera] ERROR: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
        
        print(f"[Network Camera] Stopped (Total frames processed: {self.frame_count})")
