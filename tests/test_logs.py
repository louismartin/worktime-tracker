import copy
from datetime import datetime
from unittest.mock import patch
from worktime_tracker.logs import _ALL_LOGS, Log, get_all_logs, get_logs


def test_get_logs():
    def mock_reverse_read_logs():
        return [
            Log(datetime(2021, 12, 9, 12, 4, 1), 'personal'),
            Log(datetime(2021, 12, 8, 17, 24, 18), 'personal'),
            Log(datetime(2021, 12, 8, 17, 6, 13), 'work'),
            Log(datetime(2021, 12, 7, 17, 6, 13), 'locked'),
        ]

    # Mock the reverse_read_logs function in worktime_tracker.logs
    with patch('worktime_tracker.logs.reverse_read_logs', mock_reverse_read_logs):
        _ALL_LOGS[:] = []
        get_all_logs()
        start_datetime = datetime(2021, 12, 8, 7, 0, 0)
        end_datetime = datetime(2021, 12, 9, 7, 0, 0)
        initial_logs = copy.deepcopy(_ALL_LOGS)
        print(initial_logs)
        assert get_logs(start_datetime, end_datetime) == [Log(datetime(2021, 12, 8, 17, 6, 13), 'work'), Log(datetime(2021, 12, 8, 17, 24, 18), 'personal'), Log(datetime(2021, 12, 9, 7, 0, 0), 'locked')]
        # Check that global variable _ALL_LOGS is not modified
        assert initial_logs == _ALL_LOGS