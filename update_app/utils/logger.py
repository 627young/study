import time
from PyQt5.QtWidgets import QTextEdit

class Logger:
    def __init__(self, log_area):
        self.log_area = log_area
        self.log_content = []

    def log(self, message):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        self.log_content.append(log_message)
        self.log_area.append(log_message)
        self.log_area.ensureCursorVisible()

    def clear_log(self):
        self.log_area.clear()
        self.log_content = []
