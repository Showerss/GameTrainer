import logging
import os
from datetime import datetime


class Logger:
    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"session_{timestamp}.log")

        self._logger = logging.getLogger("GameTrainer")
        self._logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        file_handler.setFormatter(formatter)

        self._logger.addHandler(file_handler)
        self._gui_callback = None

    def set_gui_logger(self, callback):
        """Connects GUI window to logger output."""
        self._gui_callback = callback

    def log(self, message: str):
        self._logger.info(message)
        if self._gui_callback:
            self._gui_callback(message)
