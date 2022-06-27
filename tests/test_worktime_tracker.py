from datetime import datetime, timedelta

from worktime_tracker.worktime_tracker import WorktimeTracker, get_average_worktime_at, get_days
from worktime_tracker.date_utils import get_day_start, get_day_end


# TODO: Check how to use fixtures
def test_worktime_tracker():
    worktime_tracker = WorktimeTracker()
    worktime_tracker.check_state()
    print("\n".join(worktime_tracker.get_week_summaries()))


def test_get_average_worktime_at():
    days = get_days()
    assert get_average_worktime_at(days, (get_day_start(datetime.now()) + timedelta(seconds=10)).time()) < 3600
    assert get_average_worktime_at(days, (get_day_end(datetime.now()) - timedelta(seconds=10)).time()) > 3600
