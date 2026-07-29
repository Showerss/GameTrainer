"""
Logger - Timestamped session logging for GameTrainer

Teacher Note: This module creates timestamped log files for each training session.
This helps you understand what the agent was "thinking" and debug issues.

All logs are saved to the logs/ directory with timestamps.
"""

import logging
import os
from datetime import datetime


class Logger:
    """
    Creates timestamped session logs for training analysis.

    Usage:
        with Logger() as logger:
            logger.log("Agent started training")
            logger.log("Reward: +1.0 for picking up item")

    The `with` form is preferred: it closes the log file for you. Without it,
    call close() by hand — on Windows the file cannot be deleted while open.
    """

    def __init__(self, log_dir="logs"):
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.log_file = os.path.join(log_dir, f"session_{timestamp}.log")

        self._logger = logging.getLogger("GameTrainer")
        self._logger.setLevel(logging.DEBUG)

        # logging.getLogger() hands back one shared object for the whole process,
        # so a handler left behind by an earlier Logger would still be pointing at
        # that earlier session's file. Drop any leftovers before adding ours.
        for stale in list(self._logger.handlers):
            self._logger.removeHandler(stale)
            stale.close()

        # Kept on the instance so close() can release the file again.
        self._handler = logging.FileHandler(self.log_file, encoding='utf-8')
        self._handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
        self._handler.setFormatter(formatter)

        self._logger.addHandler(self._handler)

        self._gui_callback = None

    def set_gui_logger(self, callback):
        """Connects GUI window to logger output."""
        self._gui_callback = callback

    def log(self, message: str):
        """Log a message to file and optionally to GUI."""
        self._logger.info(message)
        if self._gui_callback:
            self._gui_callback(message)

    def close(self):
        """Release the log file. Safe to call twice."""
        if self._handler is not None:
            self._logger.removeHandler(self._handler)
            self._handler.close()
            self._handler = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
