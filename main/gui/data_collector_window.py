import customtkinter as ctk
import cv2
import os
import time
import numpy as np
from PIL import Image, ImageTk
from core.gesture_engine import GestureEngine

class DataCollectorWindow(ctk.CTkToplevel):
    def __init__(self, parent, engine):
        super().__init__(parent)
        self.title("Data Collector - MagicHand 🖐")
        self.geometry("800x600")
        self.engine = engine
        self.parent = parent
        
        # Configuration
        self.dataset_dir = "dataset"
        self.img_size = 128
        self.frames_per_sequence = 16
        
        # State
        self.recording = False
        self.frame_count = 0
        self.current_seq_dir = ""
        self.label = ""
        self.seq_counter = 0
        
        self._setup_ui()
        
        # Start update loop
        self.update_loop()

    def _setup_ui(self):
        # 1. Input Section
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(fill="x", padx=20, pady=10)
        
        self.label_lbl = ctk.CTkLabel(self.input_frame, text="Gesture Label:", font=("Arial", 14))
        self.label_lbl.pack(side="left", padx=10)
        
        self.label_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., SwipeLeft", width=200)
        self.label_entry.pack(side="left", padx=10)
        
        self.record_btn = ctk.CTkButton(self.input_frame, text="Record Sequence (R)", command=self.start_recording)
        self.record_btn.pack(side="right", padx=10)
        
        # 2. Display Section
        self.display_frame = ctk.CTkFrame(self)
        self.display_frame.pack(expand=True, fill="both", padx=20, pady=10)
        
        self.video_label = ctk.CTkLabel(self.display_frame, text="No Video Feed")
        self.video_label.pack(side="left", expand=True, fill="both", padx=5)
        
        self.crop_label = ctk.CTkLabel(self.display_frame, text="Hand Crop", width=128, height=128, fg_color="gray")
        self.crop_label.pack(side="right", padx=20)
        
        # 3. Status
        self.status_lbl = ctk.CTkLabel(self, text="Ready", font=("Arial", 12))
        self.status_lbl.pack(pady=5)
        
        # Keyboard binding
        self.bind("<KeyPress-r>", lambda e: self.start_recording())
        self.bind("<KeyPress-R>", lambda e: self.start_recording())

    def start_recording(self):
        if self.recording:
            return
            
        self.label = self.label_entry.get().strip()
        if not self.label:
            self.status_lbl.configure(text="Error: Enter a label first!", text_color="red")
            return
            
        save_dir = os.path.join(self.dataset_dir, self.label)
        os.makedirs(save_dir, exist_ok=True)
        
        # Auto-increment sequence ID
        existing_seqs = [d for d in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, d)) and d.startswith("seq_")]
        self.seq_counter = len(existing_seqs)
        
        self.current_seq_dir = os.path.join(save_dir, f"seq_{self.seq_counter:03d}")
        os.makedirs(self.current_seq_dir, exist_ok=True)
        
        self.recording = True
        self.frame_count = 0
        self.status_lbl.configure(text=f"Recording Sequence {self.seq_counter}...", text_color="orange")

    def update_loop(self):
        if not self.winfo_exists():
            return
            
        # Try to get frame from parent's result queue if possible, or engine's latest
        # In this architecture, it's easier to tap into main_window's result_queue
        try:
            frame, result = self.parent.result_queue.get_nowait()
            
            # Process Frame for display
            display_frame = frame.copy()
            landmarks_px = self.engine.extract_landmarks(result, frame.shape)
            
            hand_crop_img = None
            
            if landmarks_px:
                # Draw landmarks
                for x, y in landmarks_px:
                    cv2.circle(display_frame, (int(x), int(y)), 2, (0, 255, 0), -1)
                
                # Get Bounding Box
                h, w, _ = frame.shape
                x1, y1, x2, y2 = self.engine.get_bbox_from_landmarks(landmarks_px, h, w)
                cv2.rectangle(display_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                
                # Crop Hand
                hand_crop = frame[y1:y2, x1:x2]
                if hand_crop.size > 0:
                    hand_crop = cv2.resize(hand_crop, (self.img_size, self.img_size))
                    
                    # Recording Logic
                    if self.recording:
                        frame_path = os.path.join(self.current_seq_dir, f"{self.frame_count:02d}.jpg")
                        cv2.imwrite(frame_path, hand_crop)
                        self.frame_count += 1
                        
                        if self.frame_count >= self.frames_per_sequence:
                            self.recording = False
                            self.status_lbl.configure(text=f"Sequence {self.seq_counter} saved!", text_color="green")
                    
                    # Update crop preview
                    hand_crop_pil = Image.fromarray(cv2.cvtColor(hand_crop, cv2.COLOR_BGR2RGB))
                    hand_crop_img = ctk.CTkImage(light_image=hand_crop_pil, dark_image=hand_crop_pil, size=(128, 128))
            else:
                if self.recording:
                    self.status_lbl.configure(text="No hand detected! Recording paused...", text_color="red")
            
            # Update Main Video
            h, w = display_frame.shape[:2]
            img = Image.fromarray(cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(w//1.2, h//1.2))
            
            self.video_label.configure(image=ctk_img, text="")
            self.video_label.image = ctk_img
            
            if hand_crop_img:
                self.crop_label.configure(image=hand_crop_img, text="")
                self.crop_label.image = hand_crop_img
                
        except:
            pass
            
        self.after(30, self.update_loop)
