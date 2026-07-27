"""
Lock the promises of Logger.

Two of these pin bugs that failed *silently* until they didn't:

  - The log file must be released when we're done with it. A leaked file
    handle raises nothing at all on Linux; on Windows it surfaces far away,
    as a PermissionError when something later tries to delete the file.
  - A second Logger must write to its OWN file. logging.getLogger() returns
    one shared object for the whole process, so a handler left behind by an
    earlier Logger would quietly capture the new one's messages and the
    log_dir you passed would be ignored. Nothing anywhere would raise.
"""

import sys
from pathlib import Path
from tempfile import TemporaryDirectory

# Project root = parent of tests/
_project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_project_root))
from src.gametrainer.logger import Logger


def test_log_creates_file_with_message():
    with TemporaryDirectory() as tmpdir:
        with Logger(log_dir=tmpdir) as logger:
            logger.log("hello")
        log_files = list(Path(tmpdir).glob("session_*.log"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "hello" in content


def test_close_releases_the_file():
    """After close(), the file can be deleted. This is the Windows failure."""
    with TemporaryDirectory() as tmpdir:
        logger = Logger(log_dir=tmpdir)
        logger.log("hello")
        logger.close()

        log_file = Path(logger.log_file)
        log_file.unlink()  # raises PermissionError on Windows if still open
        assert not log_file.exists()


def test_close_is_safe_to_call_twice():
    with TemporaryDirectory() as tmpdir:
        logger = Logger(log_dir=tmpdir)
        logger.close()
        logger.close()  # must not raise


def test_second_logger_writes_to_its_own_file():
    """The shared-logger bug: the second Logger used to write to the first's file."""
    with TemporaryDirectory() as first_dir, TemporaryDirectory() as second_dir:
        with Logger(log_dir=first_dir) as first:
            first.log("from the first")

        with Logger(log_dir=second_dir) as second:
            second.log("from the second")

        first_text = Path(first.log_file).read_text()
        second_text = Path(second.log_file).read_text()

        assert "from the first" in first_text
        assert "from the second" not in first_text
        assert "from the second" in second_text
