from pynput import mouse
import logging
import time

class MouseListener:
    def __init__(self, callback):
        self.callback = callback
        self.listener = None
        self.last_click_time = 0
        self.double_click_threshold = 0.4  # seconds

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            current_time = time.time()
            if current_time - self.last_click_time < self.double_click_threshold:
                logging.info(f"Double-Click detected at ({x}, {y})")
                self.callback(x, y)
                # Reset to avoid triple-click triggering twice
                self.last_click_time = 0
            else:
                self.last_click_time = current_time

    def start(self):
        self.listener = mouse.Listener(on_click=self.on_click)
        self.listener.start()
        logging.info("Mouse listener started (Double Click mode).")

    def stop(self):
        if self.listener:
            self.listener.stop()
        logging.info("Mouse listener stopped.")
