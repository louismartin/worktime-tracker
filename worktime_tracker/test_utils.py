from contextlib import contextmanager
import tempfile
from pathlib import Path
from unittest.mock import patch

from worktime_tracker.logs import _ALL_LOGS, write_log


@contextmanager
def mock_log_file(mocked_logs):
    """
    Context manager to mock log file for testing by changing the global constant LOGS_PATH to a temporary file.
    It will then write the dummy logs to the temporary file.

    Example usage:
    mock_log_file([
        Log(datetime(2021, 12, 7, 17, 6, 13), "locked"),
        Log(datetime(2021, 12, 8, 17, 6, 13), "work"),
        Log(datetime(2021, 12, 8, 17, 24, 18), "personal"),
        Log(datetime(2021, 12, 9, 12, 4, 1), "personal"),
    ])
    """
    _ALL_LOGS[:] = []  # Reset cached logs
    # Create a temp dir instead of a temp file because the rewrite_history() function can create additional files
    # in the same dir as the logs file and we want them to be removed when exiting
    with tempfile.TemporaryDirectory() as temp_dir:
        mocked_logs_path = Path(temp_dir) / "mocked_logs.tsv"
        with patch("worktime_tracker.logs.LOGS_PATH", mocked_logs_path):
            for log in mocked_logs:
                write_log(log)
            yield
