import customtkinter as ctk
import threading
import cv2
import queue
import time
from PIL import Image, ImageTk
from core.gesture_engine import GestureEngine
from core.input_controller import InputController
from camera.camera import CameraThread, NetworkCamera
from core.action_dispatcher import ActionDispatcher
from camera.camera_server import get_server
import base64
from io import BytesIO
from gui.data_collector_window import DataCollectorWindow

ctk.set_appearance_mode("white")
ctk.set_default_color_theme("blue")

class GestureApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("MagicHand - Gesture Control 🖐")
        self.geometry("1000x700")
        self.resizable(False, False)
        
        # Initialize modules
        self.input_ctrl = InputController()
        self.action_dispatcher = ActionDispatcher(self.input_ctrl)
        self.engine = None 
        
        # Camera server for mobile support (WiFi only)
        self.camera_server = get_server(port=5000)
        self.camera_source = "local"  # "local" or "mobile"
        
        # Threading
        self.frame_queue = queue.Queue(maxsize=1)
        self.result_queue = queue.Queue(maxsize=1)
        self.stop_event = threading.Event()
        self.camera_thread_obj = None
        self.threads_started = False
        
        self.gesture_enabled = False
        self.current_image = None # Prevent GC

        # GUI Components
        self._setup_ui()
        
    def _setup_ui(self):
        self.grid_columnconfigure(0, weight=1)


        # 1. Header Frame
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=10)
        
        self.label = ctk.CTkLabel(self.header_frame, text="🖐 MagicHand", font=("Arial", 24, "bold"))
        self.label.pack(side="left")
        
        # Mode Selector
        self.mode_label = ctk.CTkLabel(self.header_frame, text="Mode:", font=("Arial", 14))
        self.mode_label.pack(side="left", padx=(40, 5))
        
        self.mode_menu = ctk.CTkOptionMenu(
            self.header_frame, 
            values=["Navigation", "Calibration"],
            command=self.change_mode
        )
        self.mode_menu.pack(side="left")
        self.mode_menu.set("Navigation")
        
        # Camera Source Selector
        self.camera_label = ctk.CTkLabel(self.header_frame, text="Camera:", font=("Arial", 14))
        self.camera_label.pack(side="left", padx=(20, 5))
        
        self.camera_menu = ctk.CTkOptionMenu(
            self.header_frame,
            values=["Local Webcam", "Mobile Camera"],
            command=self.change_camera_source
        )
        self.camera_menu.pack(side="left")
        self.camera_menu.set("Local Webcam")
        
        self.toggle_btn = ctk.CTkButton(
            self.header_frame,
            text="Start Camera",
            command=self.toggle_gesture,
            width=100,
            fg_color="green"
        )
        self.toggle_btn.pack(side="right", padx=10)
        
        # Data Collector Button
        self.collector_btn = ctk.CTkButton(
            self.header_frame,
            text="Record Data ⏺",
            command=self.open_data_collector,
            width=100,
            fg_color="purple"
        )
        self.collector_btn.pack(side="right", padx=10)

        # 2. Key Help (Separate Compact Bar)
        self.help_frame = ctk.CTkFrame(self, fg_color="transparent", height=25)
        self.help_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 5))
        
        self.help_lbl = ctk.CTkLabel(self.help_frame, text="Move: 5 Fingers | Scroll Down: 2 Fingers | Scroll Up: 3 Fingers | Click: Pinch", font=("Arial", 12))
        self.help_lbl.pack(side="left")

        # 3. QR Code Frame (for mobile camera)
        self.qr_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.qr_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=5)
        self.qr_frame.grid_remove()  # Hidden by default
        
        self.qr_label = ctk.CTkLabel(self.qr_frame, text="")
        self.qr_label.pack(side="left", padx=10)
        
        self.qr_text = ctk.CTkLabel(
            self.qr_frame, 
            text="Scan QR code with your mobile device\nMake sure both devices are on the same network",
            font=("Arial", 14),
            justify="left"
        )
        self.qr_text.pack(side="left", padx=10)

        # 4. Video Feed
        self.video_frame = ctk.CTkFrame(self)
        self.video_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=10)
        self.grid_rowconfigure(3, weight=1) 
        
        self.video_label = ctk.CTkLabel(self.video_frame, text="Camera Off", font=("Arial", 16))
        self.video_label.pack(expand=True, fill="both")
        
        # 4. Status Bar
        self.status_label = ctk.CTkLabel(self, text="Status: Ready", text_color="gray")
        self.status_label.grid(row=4, column=0, pady=5)

    def change_mode(self, new_mode):
        self.action_dispatcher.set_mode(new_mode)
        print(f"Mode switched to: {new_mode}")
        if new_mode == "Navigation":
             self.help_lbl.configure(text="Move: 5 Fingers | Scroll Down: 2 Fingers | Scroll Up: 3 Fingers | Click: Pinch")
        elif new_mode == "Calibration":
             self.help_lbl.configure(text="Calibration: Follow on-screen targets. Pinch to record.")
    
    def change_camera_source(self, source):
        """Handle camera source change"""
        if source == "Local Webcam":
            self.camera_source = "local"
            self.qr_frame.grid_remove()
        elif source == "Mobile Camera":
            self.camera_source = "mobile"
            self.show_qr_code()
            self.qr_frame.grid()
        
        # Restart camera if already running
        if self.gesture_enabled:
            threading.Thread(target=self._restart_camera, daemon=True).start()
    
    def show_qr_code(self):
        """Generate and display QR code for mobile connection"""
        try:
            # Start server
            self.camera_server.start()
            
            # Generate QR code
            qr_base64, url = self.camera_server.generate_qr_code()
            
            # Convert base64 to image
            qr_data = base64.b64decode(qr_base64)
            qr_image = Image.open(BytesIO(qr_data))
            qr_image = qr_image.resize((200, 200))
            
            # Display QR code
            ctk_qr = ctk.CTkImage(light_image=qr_image, dark_image=qr_image, size=(200, 200))
            self.qr_label.configure(image=ctk_qr, text="")
            self.qr_label.image = ctk_qr  # Keep reference
            
            # Update text with URL
            self.qr_text.configure(
                text=f"Scan QR code with your mobile device\n{url}\nMake sure both devices are on the same network"
            )
        except Exception as e:
            print(f"Error generating QR code: {e}")
            self.qr_text.configure(text=f"Error: {e}")
    
    def _restart_camera(self):
        """Restart camera with new source"""
        self.stop_gesture_control()
        time.sleep(0.5)
        self.start_gesture_control()


    def toggle_gesture(self):
        self.toggle_btn.configure(state="disabled")
        if not self.gesture_enabled:
            threading.Thread(target=self.start_gesture_control, daemon=True).start()
        else:
            threading.Thread(target=self.stop_gesture_control, daemon=True).start()

    def start_gesture_control(self):
        self.gesture_enabled = True
        self.stop_event.clear()
        self.status_label.configure(text="Status: Initializing...", text_color="orange")
        
        # Start Processing Thread
        if not self.threads_started:
            threading.Thread(target=self.processing_thread, daemon=True).start()
            self.threads_started = True 

        # Start appropriate camera based on source
        if self.camera_source == "local":
            # Local webcam
            self.camera_thread_obj = CameraThread(self.frame_queue, self.stop_event)
        else:
            # Mobile camera via network
            self.camera_server.start()
            self.camera_thread_obj = NetworkCamera(self.frame_queue, self.stop_event, self.camera_server)
        
        self.camera_thread_obj.start()

        self.toggle_btn.configure(text="Stop Camera", fg_color="red", state="normal")
        self.after(10, self.update_ui_loop)

    def open_data_collector(self):
        """Open the dedicated data collector window"""
        if self.engine is None:
            self.engine = GestureEngine()
            
        collector_window = DataCollectorWindow(self, self.engine)
        collector_window.focus()

    def stop_gesture_control(self):
        self.gesture_enabled = False
        self.stop_event.set()
        time.sleep(0.5)
        self.toggle_btn.configure(text="Start Camera", fg_color="green", state="normal")
        self.status_label.configure(text="Status: Stopped", text_color="gray")
        self.video_label.configure(image=None, text="Camera Off")

    def processing_thread(self):
        if self.engine is None:
            self.engine = GestureEngine()
            
        while not self.stop_event.is_set():
            if not self.gesture_enabled:
                time.sleep(0.1)
                continue
            
            try:
                frame = self.frame_queue.get(timeout=1)
            except queue.Empty:
                continue
                
            timestamp = int(time.time() * 1000)
            result = self.engine.process_frame(frame, timestamp)
            
            try:
                if self.result_queue.full():
                    try: self.result_queue.get_nowait()
                    except: pass
                self.result_queue.put((frame, result))
            except:
                pass

    def update_ui_loop(self):
        if not self.gesture_enabled:
            return

        try:
            frame, result = self.result_queue.get_nowait()
            
            if self.status_label.cget("text") == "Status: Initializing...":
                 self.status_label.configure(text="Status: Running", text_color="green")
            
            landmarks_px = self.engine.extract_landmarks(result, frame.shape)
            analysis = self.engine.analyze_gesture(landmarks_px)
            
            if landmarks_px and analysis:
                try:
                    # Get smoothed coordinates immediately for updating engine state and drawing overlay potentially?
                    # The dispatcher manages smoothing usage? 
                    # Ideally engine updates smoothing state when we ask.
                    sx, sy = self.engine.apply_smoothing(analysis["palm_pos"][0], analysis["palm_pos"][1], time.time())
                    
                    # Custom NN Prediction (RF)
                    nn_gesture, confidence = self.engine.predict_gesture_from_result(result)
                    if nn_gesture:
                        print(f"NN PREDICTION: {nn_gesture} ({confidence:.2f})")
                        cv2.putText(frame, f"NN: {nn_gesture}", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    self.action_dispatcher.process(frame, analysis, (sx, sy), nn_gesture)
                except Exception as e:
                    print(f"Dispatcher Error: {e}")
                
                # Draw Landmarks
                for (x, y) in landmarks_px:
                     cv2.circle(frame, (int(x), int(y)), 4, (0, 255, 0), -1)
            
            h, w = frame.shape[:2]
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))
            self.current_image = ctk_img
            self.video_label.configure(image=self.current_image, text="")
            
        except queue.Empty:
            pass
        
        self.after(5, self.update_ui_loop)
