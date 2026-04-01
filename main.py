"""
Air Gesture Controller v17.0 - Stable Cursor Edition
Changes:
1. 35x cursor speed (reduced for stability)
2. Anti-stutter cursor movement
3. Removed flat hand click
4. Removed Alt+Tab gesture
"""

import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import math
import time
import win32api
import win32con
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.vision import RunningMode

# Resolve hand_landmarker.task relative to this file
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_BASE_DIR, "hand_landmarker.task")

# ===== MEDIAPIPE SETUP =====
base_options = python.BaseOptions(model_asset_path=_MODEL_PATH)

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    running_mode=RunningMode.VIDEO,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)

detector = vision.HandLandmarker.create_from_options(options)


class AirGestureController:
    def __init__(self):
        # Screen
        self.screen_width = win32api.GetSystemMetrics(win32con.SM_CXSCREEN)
        self.screen_height = win32api.GetSystemMetrics(win32con.SM_CYSCREEN)
        pyautogui.FAILSAFE = False
        
        print(f"Screen: {self.screen_width}x{self.screen_height}")
        
        # Cursor
        self.cursor_x = self.screen_width // 2
        self.cursor_y = self.screen_height // 2
        
        # Anti-stutter: weighted average of positions
        self.target_x = self.cursor_x
        self.target_y = self.cursor_y
        self.smooth_factor = 0.5  # Lower = more smooth, less jitter
        
        # Click handling
        self.last_left_click = 0
        self.last_right_click = 0
        self.click_cooldown = 0.3
        
        # Scroll handling
        self.scroll_cooldown = 0.05
        self.scroll_amount = 80
        self.last_scroll_time = 0
        self.is_scrolling_up = False
        self.is_scrolling_down = False
        
        # Exit
        self.hands_joined_time = None
        
        self.running = True

    def get_hand_side(self, landmarks):
        wrist = landmarks[0]
        return "RIGHT" if wrist.x > 0.5 else "LEFT"

    def detect_pinch_middle_thumb_right(self, landmarks):
        """Detect thumb + middle finger pinch for RIGHT hand (double click)"""
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]
        ring_tip = landmarks[16]
        
        pinch_dist = math.dist([thumb_tip.x, thumb_tip.y], [middle_tip.x, middle_tip.y])
        hand_size = math.dist([ring_tip.x, ring_tip.y], [wrist.x, wrist.y])
        
        return pinch_dist < hand_size * 0.35

    def detect_pinch_middle_thumb_left(self, landmarks):
        """Detect thumb + middle finger pinch for LEFT hand"""
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        middle_tip = landmarks[12]
        index_tip = landmarks[8]
        
        pinch_dist = math.dist([thumb_tip.x, thumb_tip.y], [middle_tip.x, middle_tip.y])
        hand_size = math.dist([index_tip.x, index_tip.y], [wrist.x, wrist.y])
        
        return pinch_dist < hand_size * 0.35

    def get_thumb_scroll_direction(self, landmarks):
        """
        Get thumb scroll direction
        Returns "UP" if thumb is pointing up, "DOWN" if pointing down
        """
        wrist = landmarks[0]
        thumb_tip = landmarks[4]
        
        dy = thumb_tip.y - wrist.y
        
        if dy < -0.08:
            return "UP"
        elif dy > 0.08:
            return "DOWN"
        
        return "NONE"

    def palms_joined(self, left_landmarks, right_landmarks):
        """Both palms joined together"""
        if not left_landmarks or not right_landmarks:
            return False
        
        left_wrist = left_landmarks[0]
        right_wrist = right_landmarks[0]
        
        distance = math.dist([left_wrist.x, left_wrist.y], [right_wrist.x, right_wrist.y])
        return distance < 0.15

    def update_cursor_35x(self, landmarks):
        """35x cursor movement with anti-stutter smoothing"""
        index_tip = landmarks[8]
        
        x = index_tip.x
        y = index_tip.y
        
        # 35X RANGE
        x = (x - 0.5) * 35.0 + 0.5
        y = (y - 0.5) * 35.0 + 0.5
        
        # Map back to 0-1
        x = (x + 17) / 35.0
        y = (y + 17) / 35.0
        
        # Clamp
        x = max(0.0, min(1.0, x))
        y = max(0.0, min(1.0, y))
        
        # Convert to screen
        new_x = int(x * self.screen_width)
        new_y = int(y * self.screen_height)
        
        # Anti-stutter: weighted average (exponential moving average)
        # Lower smooth_factor = smoother but more lag
        self.target_x = new_x
        self.target_y = new_y
        
        # Apply EMA smoothing
        self.cursor_x = int(self.cursor_x + (self.target_x - self.cursor_x) * self.smooth_factor)
        self.cursor_y = int(self.cursor_y + (self.target_y - self.cursor_y) * self.smooth_factor)

    def run(self):
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print("=" * 60)
        print("Air Gesture Controller v17.0 - STABLE CURSOR")
        print("=" * 60)
        print("\n[*] FEATURES:")
        print("  - 35x cursor speed (stable)")
        print("  - Anti-stutter smoothing")
        print("  - Reliable continuous scroll")
        print("\n[>] CONTROLS:")
        print("  - RIGHT HAND MOVEMENT = Cursor (35x)")
        print("  - LEFT HAND MOVEMENT = Cursor (35x) [ASSIST]")
        print("  - RIGHT MIDDLE + THUMB = DOUBLE CLICK")
        print("  - LEFT MIDDLE + THUMB = SINGLE CLICK")
        print("  - LEFT THUMB UP (HOLD) = SCROLL UP")
        print("  - LEFT THUMB DOWN (HOLD) = SCROLL DOWN")
        print("  - JOIN BOTH PALMS = EXIT")
        print("=" * 60)
        
        cv2.namedWindow("Air Gesture Controller v17.0", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Air Gesture Controller v17.0", 1280, 720)
        
        while self.running:
            ret, frame = cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]
            
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp = int(time.time() * 1000)

            try:
                result = detector.detect_for_video(mp_image, timestamp)
            except:
                continue

            right_hand = None
            left_hand = None
            left_pinch = False
            right_middle_pinch = False
            left_thumb_dir = "NONE"
            
            if result.hand_landmarks:
                for landmarks in result.hand_landmarks:
                    side = self.get_hand_side(landmarks)
                    
                    for lm in landmarks:
                        x = int(lm.x * w)
                        y = int(lm.y * h)
                        color = (0, 255, 0) if side == "RIGHT" else (255, 255, 0)
                        cv2.circle(frame, (x, y), 4, color, -1)
                    
                    if side == "RIGHT":
                        right_hand = landmarks
                        right_middle_pinch = self.detect_pinch_middle_thumb_right(landmarks)
                    else:
                        left_hand = landmarks
                        left_pinch = self.detect_pinch_middle_thumb_left(landmarks)
                        left_thumb_dir = self.get_thumb_scroll_direction(landmarks)
            
            current_time = time.time()
            
            # EXIT: Palms joined
            if self.palms_joined(left_hand, right_hand):
                if self.hands_joined_time is None:
                    self.hands_joined_time = current_time
                elif current_time - self.hands_joined_time > 1.0:
                    print("🙏 PALMS JOINED - EXIT")
                    self.running = False
                    break
            else:
                self.hands_joined_time = None
            
            # MOVE: Both hands
            if right_hand:
                self.update_cursor_35x(right_hand)
            elif left_hand:
                self.update_cursor_35x(left_hand)
            
            # Cursor update
            win32api.SetCursorPos((self.cursor_x, self.cursor_y))
            
            # SCROLL: Continuous while thumb held
            if left_hand and left_thumb_dir != "NONE":
                if current_time - self.last_scroll_time > self.scroll_cooldown:
                    if left_thumb_dir == "UP":
                        pyautogui.scroll(self.scroll_amount)
                        self.last_scroll_time = current_time
                        self.is_scrolling_up = True
                        self.is_scrolling_down = False
                    elif left_thumb_dir == "DOWN":
                        pyautogui.scroll(-self.scroll_amount)
                        self.last_scroll_time = current_time
                        self.is_scrolling_down = True
                        self.is_scrolling_up = False
            else:
                self.is_scrolling_up = False
                self.is_scrolling_down = False
            
            # SINGLE CLICK: Left pinch (middle + thumb)
            if left_hand and left_pinch:
                if current_time - self.last_left_click > self.click_cooldown:
                    pyautogui.click(self.cursor_x, self.cursor_y)
                    self.last_left_click = current_time
                    print("👆 LEFT PINCH - Single Click")
            
            # DOUBLE CLICK: Right pinch (middle + thumb)
            if right_hand and right_middle_pinch:
                if current_time - self.last_right_click > self.click_cooldown:
                    pyautogui.doubleClick(self.cursor_x, self.cursor_y)
                    self.last_right_click = current_time
                    print("👆 RIGHT PINCH - Double Click")
            
            # UI
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
            cv2.rectangle(overlay, (0, h-80), (w, h), (0, 0, 0), -1)
            frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)
            
            # Status
            if right_hand and left_hand:
                status = "Both hands - DUAL NAV"
            elif right_hand:
                status = "Right: Move (35x) + Pinch = Double"
            elif left_hand:
                status = "Left: Move (35x) + Pinch = Single"
            else:
                status = "No hands"
            
            cv2.putText(frame, status, (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2)
            cv2.putText(frame, f"Cursor: ({self.cursor_x}, {self.cursor_y})", (w-350, 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            # Gesture indicators
            if self.is_scrolling_up:
                cv2.putText(frame, "👍 SCROLLING UP...", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif self.is_scrolling_down:
                cv2.putText(frame, "👎 SCROLLING DOWN...", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif left_thumb_dir == "UP":
                cv2.putText(frame, "👍 THUMB UP", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            elif left_thumb_dir == "DOWN":
                cv2.putText(frame, "👎 THUMB DOWN", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)
            
            if self.palms_joined(left_hand, right_hand):
                cv2.putText(frame, "🙏 PALMS = Exit", (w//2 - 80, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 150, 255), 2)
            
            cv2.putText(frame, "Dual Nav (35x) | Right: Pinch = Double | Left: Pinch = Single | HOLD Thumb Up/Down = Scroll | Palms = Exit",
                       (20, h-25), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
            
            cv2.imshow("Air Gesture Controller v17.0", frame)
            
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cap.release()
        cv2.destroyAllWindows()
        print("\n✓ Stopped")


if __name__ == "__main__":
    controller = AirGestureController()
    controller.run()
