from contextlib import contextmanager
import tempfile
from pathlib import Path
from unittest.mock import patch

from worktime_tracker.logs import write_log


@contextmanager
def mock_log_file(mocked_logs):
    """
    Context manager to mock log file for testing by changing the global constant LOGS_PATH to a temporary file.
    It will then write the dummy logs to the temporary file.
    Also clears the History singleton and mocks time.time() to return a timestamp
    just after the last mocked log (so the dummy "now" interval doesn't span years).
    """
    from worktime_tracker.history import History

    fake_timestamp = mocked_logs[-1].timestamp + 60 if mocked_logs else 0

    with tempfile.TemporaryDirectory() as temp_dir:
        mocked_logs_path = Path(temp_dir) / "mocked_logs.tsv"
        History.clear()
        with (
            patch("worktime_tracker.logs.LOGS_PATH", mocked_logs_path),
            patch("worktime_tracker.history.time.time", return_value=fake_timestamp),
        ):
            for log in mocked_logs:
                write_log(log)
            yield
        History.clear()
