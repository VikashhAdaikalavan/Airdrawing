import cv2
import mediapipe as mp
import numpy as np
import tkinter as tk
from tkinter import colorchooser, messagebox
from PIL import Image, ImageTk
import threading
import time

class AirDrawingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Draw in Air - Enhanced Edition")
        self.root.geometry("1400x800")
        
        self.mode = "PAUSED"
        self.brush_color = (0, 255, 0)
        self.brush_size = 5
        self.eraser_size = 30
        self.canvas = None
        self.prev_x, self.prev_y = None, None
        
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils
        
        self.smoothing_buffer = []
        self.buffer_size = 5
        
        self.setup_ui()
        
        self.running = True
        self.video_thread = threading.Thread(target=self.process_video)
        self.video_thread.daemon = True
        self.video_thread.start()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_ui(self):
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        video_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.RIDGE, bd=2)
        video_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        tk.Label(video_frame, text="Camera Feed", bg="#34495e", fg="white", 
                font=("Arial", 14, "bold")).pack(pady=5)
        
        self.video_label = tk.Label(video_frame, bg="black")
        self.video_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        control_frame = tk.Frame(main_frame, bg="#34495e", relief=tk.RIDGE, bd=2, width=320)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        control_frame.pack_propagate(False)
        
        tk.Label(control_frame, text="Controls", bg="#34495e", fg="white",
                font=("Arial", 16, "bold")).pack(pady=15)
        
        self.status_frame = tk.Frame(control_frame, bg="#34495e")
        self.status_frame.pack(pady=10)
        
        tk.Label(self.status_frame, text="Mode:", bg="#34495e", fg="white",
                font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        
        self.status_label = tk.Label(self.status_frame, text="PAUSED", 
                                     bg="#95a5a6", fg="white", font=("Arial", 12, "bold"),
                                     width=10, relief=tk.RAISED)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        instructions_frame = tk.Frame(control_frame, bg="#2c3e50", relief=tk.SUNKEN, bd=2)
        instructions_frame.pack(pady=10, padx=10, fill=tk.X)
        
        tk.Label(control_frame, text="Brush Size:", bg="#34495e", fg="white",
                font=("Arial", 11, "bold")).pack(pady=(15, 5))
        
        self.size_scale = tk.Scale(control_frame, from_=2, to=20, orient=tk.HORIZONTAL,
                                   bg="#34495e", fg="white", highlightthickness=0,
                                   command=self.change_brush_size, length=200)
        self.size_scale.set(5)
        self.size_scale.pack(pady=5)
        
        tk.Label(control_frame, text="Eraser Size:", bg="#34495e", fg="white",
                font=("Arial", 11, "bold")).pack(pady=(10, 5))
        
        self.eraser_scale = tk.Scale(control_frame, from_=10, to=60, orient=tk.HORIZONTAL,
                                     bg="#34495e", fg="white", highlightthickness=0,
                                     command=self.change_eraser_size, length=200)
        self.eraser_scale.set(30)
        self.eraser_scale.pack(pady=5)
        
        tk.Button(control_frame, text="Change Color", command=self.choose_color,
                 bg="#3498db", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.RAISED, bd=3, width=15, height=2).pack(pady=10)
        
        self.color_display = tk.Frame(control_frame, bg="#00ff00", 
                                      height=40, relief=tk.SUNKEN, bd=3)
        self.color_display.pack(pady=5, padx=20, fill=tk.X)
        
        btn_frame = tk.Frame(control_frame, bg="#34495e")
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Clear Canvas", command=self.clear_canvas,
                 bg="#e74c3c", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.RAISED, bd=3, width=15, height=2).pack(pady=5)
        
        tk.Button(btn_frame, text="Save Drawing", command=self.save_drawing,
                 bg="#27ae60", fg="white", font=("Arial", 11, "bold"),
                 relief=tk.RAISED, bd=3, width=15, height=2).pack(pady=5)
        
        info_frame = tk.Frame(control_frame, bg="#2c3e50", relief=tk.SUNKEN, bd=2)
        info_frame.pack(side=tk.BOTTOM, pady=10, padx=10, fill=tk.X)
        
        tk.Label(info_frame, text="Tip: Use good lighting\nfor best results", 
                bg="#2c3e50", fg="#95a5a6", font=("Arial", 9, "italic"),
                justify=tk.LEFT).pack(pady=5, padx=5)
    
    def count_extended_fingers(self, landmarks, w, h):
        finger_tips = [8, 12, 16, 20]
        finger_pips = [6, 10, 14, 18]
        
        extended_count = 0
        
        for tip, pip in zip(finger_tips, finger_pips):
            tip_y = landmarks[tip].y
            pip_y = landmarks[pip].y
            
            if tip_y < pip_y - 0.02:
                extended_count += 1
        
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        
        if abs(thumb_tip.x - thumb_ip.x) > 0.05:
            extended_count += 1
        
        return extended_count
    
    def detect_gesture(self, landmarks, w, h):
        extended_fingers = self.count_extended_fingers(landmarks, w, h)
        
        index_tip = landmarks[8]
        index_mcp = landmarks[5]
        
        middle_tip = landmarks[12]
        
        index_extended = index_tip.y < index_mcp.y - 0.02
        
        middle_folded = middle_tip.y > index_mcp.y
        
        if extended_fingers >= 4:
            return "PAUSED"
        
        elif index_extended and middle_folded and extended_fingers <= 2:
            return "DRAWING"
        
        else:
            return "ERASING"
    
    def process_video(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            if self.canvas is None:
                self.canvas = np.zeros_like(frame)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(
                        frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=2),
                        self.mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2)
                    )
                    
                    landmarks = hand_landmarks.landmark
                    
                    gesture = self.detect_gesture(landmarks, w, h)
                    self.mode = gesture
                    
                    index_tip = landmarks[8]
                    index_x = int(index_tip.x * w)
                    index_y = int(index_tip.y * h)
                    
                    if gesture == "ERASING":
                        wrist = landmarks[0]
                        middle_mcp = landmarks[9]
                        palm_x = int((wrist.x + middle_mcp.x) / 2 * w)
                        palm_y = int((wrist.y + middle_mcp.y) / 2 * h)
                        cursor_x, cursor_y = palm_x, palm_y
                    else:
                        cursor_x, cursor_y = index_x, index_y
                    
                    if gesture == "DRAWING":
                        self.update_status("DRAWING", "#00ff3c")
                        
                        self.smoothing_buffer.append((cursor_x, cursor_y))
                        if len(self.smoothing_buffer) > self.buffer_size:
                            self.smoothing_buffer.pop(0)
                        
                        smooth_x = int(np.mean([p[0] for p in self.smoothing_buffer]))
                        smooth_y = int(np.mean([p[1] for p in self.smoothing_buffer]))
                        
                        if self.prev_x is not None and self.prev_y is not None:
                            cv2.line(self.canvas, (self.prev_x, self.prev_y),
                                   (smooth_x, smooth_y), self.brush_color, 
                                   self.brush_size)
                        
                        self.prev_x, self.prev_y = smooth_x, smooth_y
                        
                        cv2.circle(frame, (smooth_x, smooth_y), 
                                 self.brush_size + 3, self.brush_color, 2)
                        cv2.circle(frame, (smooth_x, smooth_y), 
                                 3, self.brush_color, -1)
                    
                    elif gesture == "ERASING":
                        self.update_status("ERASING", "#e67e22")
                        
                        self.smoothing_buffer.append((cursor_x, cursor_y))
                        if len(self.smoothing_buffer) > self.buffer_size:
                            self.smoothing_buffer.pop(0)
                        
                        smooth_x = int(np.mean([p[0] for p in self.smoothing_buffer]))
                        smooth_y = int(np.mean([p[1] for p in self.smoothing_buffer]))
                        
                        cv2.circle(self.canvas, (smooth_x, smooth_y), 
                                 self.eraser_size, (0, 0, 0), -1)
                        
                        self.prev_x, self.prev_y = smooth_x, smooth_y
                        
                        cv2.circle(frame, (smooth_x, smooth_y), 
                                 self.eraser_size, (0, 165, 255), 3)
                        cv2.circle(frame, (smooth_x, smooth_y), 
                                 5, (0, 165, 255), -1)
                    
                    else:
                        self.update_status("PAUSED", "#e74c3c")
                        self.prev_x, self.prev_y = None, None
                        self.smoothing_buffer.clear()
                        
                        cv2.circle(frame, (cursor_x, cursor_y), 10, (0, 0, 255), 2)
            else:
                self.mode = "PAUSED"
                self.update_status("NO HAND", "#95a5a6")
                self.prev_x, self.prev_y = None, None
                self.smoothing_buffer.clear()
            
            mask = np.any(self.canvas != 0, axis=2)
            frame[mask] = cv2.addWeighted(frame, 0.3, self.canvas, 0.7, 0)[mask]
            
            mode_text = f"Mode: {self.mode}"
            cv2.putText(frame, mode_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       1, (255, 255, 255), 2, cv2.LINE_AA)
            
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(image=img)
            
            self.video_label.img_tk = img_tk
            self.video_label.configure(image=img_tk)
            
            time.sleep(0.01)
    
    def update_status(self, text, color):
        self.status_label.config(text=text, bg=color)
    
    def change_brush_size(self, val):
        self.brush_size = int(val)
    
    def change_eraser_size(self, val):
        self.eraser_size = int(val)
    
    def choose_color(self):
        color = colorchooser.askcolor(title="Choose Brush Color")
        if color[0]:
            rgb = color[0]
            self.brush_color = (int(rgb[2]), int(rgb[1]), int(rgb[0]))
            
            hex_color = color[1]
            self.color_display.config(bg=hex_color)
    
    def clear_canvas(self):
        if self.canvas is not None:
            self.canvas = np.zeros_like(self.canvas)
        messagebox.showinfo("Clear", "Canvas cleared!")
    
    def save_drawing(self):
        if self.canvas is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"air_drawing_{timestamp}.png"
            
            white_bg = np.ones_like(self.canvas) * 255
            mask = np.any(self.canvas != 0, axis=2)
            white_bg[mask] = self.canvas[mask]
            
            cv2.imwrite(filename, white_bg)
            messagebox.showinfo("Save", f"Drawing saved as {filename}")
    
    def on_closing(self):
        self.running = False
        time.sleep(0.2)
        self.cap.release()
        self.hands.close()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AirDrawingApp(root)
    root.mainloop()