import sys
from pathlib import Path
from tempfile import TemporaryDirectory


# Make the core logger module importable.
sys.path.append(str(Path(__file__).resolve().parents[1] / "src/python"))
from core.logger import Logger


def test_log_creates_file_with_message():
    with TemporaryDirectory() as tmpdir:
        logger = Logger(log_dir=tmpdir)
        logger.log("hello")
        log_files = list(Path(tmpdir).glob("session_*.log"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "hello" in content
