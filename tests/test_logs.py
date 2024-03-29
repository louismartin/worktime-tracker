import copy
from datetime import datetime

from worktime_tracker.history import History, Interval
from worktime_tracker.logs import (
    Log,
    get_all_logs,
    rewrite_history,
)
from worktime_tracker.worktime_tracker import get_worktime_between
from worktime_tracker.test_utils import mock_log_file


def test_get_intervals():
    mocked_logs = [
        Log(datetime(2021, 12, 7, 17, 6, 13), "locked"),
        Log(datetime(2021, 12, 8, 17, 6, 13), "work"),
        Log(datetime(2021, 12, 8, 17, 24, 18), "personal"),
        Log(datetime(2021, 12, 9, 12, 4, 1), "personal"),
    ]
    with mock_log_file(mocked_logs):
        initial_logs = copy.deepcopy(get_all_logs())
        print(initial_logs)
        start_datetime = datetime(2021, 12, 8, 7, 0, 0)
        end_datetime = datetime(2021, 12, 9, 7, 0, 0)
        history = History(dont_read_before=None)
        intervals = history.all_intervals
        assert Interval.get_intervals_between(intervals, start_datetime, end_datetime) == [
            Interval(Log(datetime(2021, 12, 8, 7, 0, 0), "locked"), Log(datetime(2021, 12, 8, 17, 6, 13), "work")),
            Interval(Log(datetime(2021, 12, 8, 17, 6, 13), "work"), Log(datetime(2021, 12, 8, 17, 24, 18), "personal")),
            Interval(
                Log(datetime(2021, 12, 8, 17, 24, 18), "personal"), Log(datetime(2021, 12, 9, 7, 0, 0), "personal")
            ),
        ]
        # Check that global variable _ALL_LOGS is not modified
        assert initial_logs == get_all_logs()


def test_get_all_intervals():
    mocked_logs = [
        Log(datetime(2021, 12, 7, 17, 6, 13), "locked"),
        Log(datetime(2021, 12, 8, 17, 6, 13), "work"),
        Log(datetime(2021, 12, 8, 17, 24, 18), "personal"),
        Log(datetime(2021, 12, 9, 12, 4, 1), "personal"),
    ]
    with mock_log_file(mocked_logs):
        history = History(dont_read_before=None)
        intervals = history.all_intervals
        assert len(intervals) == len(mocked_logs)
        assert intervals[-1].start_log == mocked_logs[-1]


def test_rewrite_history():
    mocked_logs = [
        Log(datetime(2021, 12, 7, 8, 0, 0), "locked"),
        Log(datetime(2021, 12, 7, 11, 0, 0), "work"),
        Log(datetime(2021, 12, 7, 11, 30, 0), "personal"),
        Log(datetime(2021, 12, 7, 12, 0, 0), "work"),
        Log(datetime(2021, 12, 7, 12, 30, 0), "personal"),
    ]
    with mock_log_file(mocked_logs):
        assert get_worktime_between(datetime(2021, 12, 7, 8, 0, 0), datetime(2021, 12, 7, 13, 0, 0)) == 60 * 60
        assert get_worktime_between(datetime(2021, 12, 7, 11, 0, 0), datetime(2021, 12, 7, 12, 0, 0)) == 30 * 60
        rewrite_history(datetime(2021, 12, 7, 10, 0, 0), datetime(2021, 12, 7, 12, 10, 0), "work")
        # Work from 10:00 to 12:30
        assert get_worktime_between(datetime(2021, 12, 7, 8, 0, 0), datetime(2021, 12, 7, 13, 0, 0)) == 150 * 60
        rewrite_history(datetime(2021, 12, 7, 11, 30, 0), datetime(2021, 12, 7, 12, 10, 0), "personal")
        # Work from 10:00 to 11:30 and from 12:10 to 12:30
        assert get_worktime_between(datetime(2021, 12, 7, 8, 0, 0), datetime(2021, 12, 7, 13, 0, 0)) == 110 * 60
