from datetime import datetime

import pytest

from worktime_tracker.tools import get_productivity_plot, get_todays_productivity_plot, get_ghost_plot
from worktime_tracker.test_utils import mock_log_file
from worktime_tracker.logs import Log


def test_get_todays_productivity_plot():
    """Check that get_todays_productivity_plot does not raise an error."""
    assert get_todays_productivity_plot() is not None


def test_get_productivity_plot():
    mocked_logs = [
        Log(datetime(2021, 12, 7, 11, 0, 0), "work"),
        Log(datetime(2021, 12, 7, 11, 30, 0), "personal"),
    ]
    with mock_log_file(mocked_logs):
        fig = get_productivity_plot(mocked_logs[0].datetime, mocked_logs[-1].datetime)
        # Each histogram bar is no more than 15 minutes
        assert max(fig.data[0].y) == 15
        # The sum of all histogram bars (in minutes) must be the total work time
        assert sum(fig.data[0].y) == 30


def test_get_ghost_plot():
    assert get_ghost_plot(length=50) is not None
