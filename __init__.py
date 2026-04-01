"""
YOAIR - Air Gesture Controller
A Python library for controlling your cursor with hand gestures.

Usage:
    import YOAIR
    YOAIR.start()

Controls:
    - Right/Left hand movement = Move cursor (35x)
    - Right middle+thumb pinch = Double click
    - Left middle+thumb pinch  = Single click
    - Left thumb UP (hold)    = Scroll up
    - Left thumb DOWN (hold)   = Scroll down
    - Both palms joined        = Exit
"""

from YOAIR.main import AirGestureController

_controller = None

def start() -> None:
    """Start the Air Gesture Controller."""
    global _controller
    _controller = AirGestureController()
    _controller.run()

def stop() -> None:
    """Stop the Air Gesture Controller."""
    global _controller
    if _controller is not None:
        _controller.running = False
