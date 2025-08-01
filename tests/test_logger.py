import unittest
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Add core directory to path so we can import logger
sys.path.append(str(Path(__file__).resolve().parents[1] / "src/python/core"))
from logger import Logger

class TestLoggerFileOutput(unittest.TestCase):
    def test_log_creates_file_with_message(self):
        with TemporaryDirectory() as tmpdir:
            logger = Logger(log_dir=tmpdir)
            logger.log("hello")
            log_files = list(Path(tmpdir).glob("session_*.log"))
            self.assertEqual(len(log_files), 1)
            content = log_files[0].read_text()
            self.assertIn("hello", content)

if __name__ == "__main__":
    unittest.main()
