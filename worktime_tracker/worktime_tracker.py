from collections import defaultdict
from functools import lru_cache
from datetime import datetime, timedelta, time as datetime_time  # Avoid confusion between time and datetime
import time
import numpy as np

from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.spaces import get_state
from worktime_tracker.constants import WORK_STATES
from worktime_tracker.date_utils import (
    get_weekday_start_and_end,
    WEEKDAYS,
    get_current_weekday,
    coerce_to_datetime,
    get_day_start,
    get_day_end,
)
from worktime_tracker.logs import (
    Log,
    get_all_intervals,
    get_intervals,
    read_last_log,
    maybe_write_log,
    write_last_check,
    read_last_check_timestamp,
    get_intervals_between,
)


def get_cum_times_per_state(start_datetime: datetime, end_datetime: datetime):
    assert start_datetime < end_datetime
    intervals = get_intervals(start_datetime, end_datetime)
    cum_times_per_state = defaultdict(float)
    for interval in intervals:
        cum_times_per_state[interval.state] += interval.duration
    return cum_times_per_state


def get_work_time(start_datetime: datetime, end_datetime: datetime):
    cum_times = get_cum_times_per_state(start_datetime, end_datetime)
    return sum(cum_times[state] for state in WORK_STATES)


def get_work_time_from_intervals(intervals):
    return sum(interval.duration for interval in intervals if interval.state in WORK_STATES)


def maybe_fix_unfinished_work_state():
    """If the app was killed during a work state, it will count everything from this moment as work.
    We want to fix it if this is the case"""
    timestamp = time.time()
    last_check_timestamp = read_last_check_timestamp()
    last_log = read_last_log()
    if timestamp - last_check_timestamp < 60:
        return
    if last_log.state not in WORK_STATES:
        return
    write_last_check(timestamp)
    maybe_write_log(Log(last_check_timestamp + 1, "locked"))


class WorktimeTracker:

    targets = [
        0,  # Sunday
        6.25 * 3600,  # Monday
        6.25 * 3600,  # Tuesday
        6.25 * 3600,  # Wednesday
        6.25 * 3600,  # Thursday
        5 * 3600,  # Friday
        0,  # Saturday
    ]

    def __init__(self, read_only=False):
        maybe_fix_unfinished_work_state()
        self.read_only = read_only

    @staticmethod
    def is_work_state(state):
        return state in WORK_STATES

    @property
    def current_state(self):
        return read_last_log().state

    # TODO: Move all these static methods to functions?
    @staticmethod
    def get_work_ratio_since_timestamp(start_timestamp):
        end_datetime = datetime.now()
        work_time = get_work_time(start_datetime=coerce_to_datetime(start_timestamp), end_datetime=datetime.now())
        return work_time / (end_datetime.timestamp() - start_timestamp)

    @staticmethod
    def get_work_time_from_weekday(weekday):
        weekday_start, weekday_end = get_weekday_start_and_end(weekday)
        return get_work_time(weekday_start, weekday_end)

    def maybe_append_and_write_log(self, log):
        if self.read_only:
            return
        maybe_write_log(log)

    def check_state(self):
        """Checks the current state and update the logs. Returns a boolean of whether the state changed or not"""
        # TODO: We should split the writing logic and the state checking logic
        last_log = read_last_log()
        timestamp = time.time()
        write_last_check(timestamp)
        state = get_state()
        self.maybe_append_and_write_log(Log(timestamp, state))
        return state != last_log.state

    def get_weekday_summary(self, weekday_idx):
        weekday = WEEKDAYS[weekday_idx]
        work_time = self.get_work_time_from_weekday(weekday_idx)
        target = WorktimeTracker.targets[weekday_idx]
        ratio = work_time / target if target != 0 else 1
        return f"{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(work_time)})"

    def get_week_overtime_summary(self):
        work_time = sum([self.get_work_time_from_weekday(weekday_idx) for weekday_idx in range(get_current_weekday())])
        target = sum([WorktimeTracker.targets[weekday_idx] for weekday_idx in range(get_current_weekday())])
        return f"Week overtime: {seconds_to_human_readable(work_time - target)}"

    def get_instant_summary(self):
        work_ratio_last_period = self.get_work_ratio_since_timestamp(time.time() - 3600 / 2)
        work_time_today = self.get_work_time_from_weekday(get_current_weekday())
        return f"{int(100 * work_ratio_last_period)}% - {seconds_to_human_readable(work_time_today)}"

    def get_week_summaries(self):
        """Nicely formatted day summaries for displaying to the user"""
        summaries = [self.get_weekday_summary(weekday_idx) for weekday_idx in range(get_current_weekday() + 1)][::-1]
        summaries += [self.get_week_overtime_summary()]
        return summaries


class Day:
    """Class that regroups intervals of a day"""

    def __init__(self, intervals) -> None:
        self.intervals = intervals
        self.day_start = get_day_start(intervals[0].start_datetime)
        self.day_end = get_day_end(intervals[0].end_datetime)
        assert [get_day_start(interval.start_datetime) == self.day_start for interval in intervals]
        assert [get_day_end(interval.end_datetime) == self.day_end for interval in intervals]

    @property
    def work_intervals(self):
        return [interval for interval in self.intervals if interval.is_work_interval]

    def get_work_time_at(self, dt_time):
        assert isinstance(dt_time, datetime_time)

        dt = datetime.combine(self.day_start, dt_time)
        if dt <= self.day_start:  # Hours after midnight should count as the next day
            dt += timedelta(days=1)
        intervals_before_dt = get_intervals_between(self.work_intervals, self.day_start, dt)
        assert self.day_start <= dt
        return sum([interval.work_time for interval in intervals_before_dt])

    @property
    def work_time(self):
        return sum([interval.work_time for interval in self.work_intervals])

    def is_week_day(self):
        return self.day_start.weekday() < 5

    def is_work_day(self):
        # TODO: Maybe use weekdays as well
        return self.is_week_day() and self.work_time > 4 * 3600


def split_interval_by_day(interval):
    """Split intervals that spans multiple days into multiple intervals or return [interval] if it's not needed

    args: interval
    return: list of intervals
    """
    day_end = get_day_end(interval.start_datetime)
    if interval.end_datetime < day_end:
        return [interval]
    interval_in_day, interval_after_day = interval.split(day_end)
    return [interval_in_day] + split_interval_by_day(interval_after_day)


def split_intervals_by_day(intervals):
    return [split_interval for interval in intervals for split_interval in split_interval_by_day(interval)]


def group_intervals_by_day(intervals):
    """Group intervals by day

    args: intervals
    return: list of Day objects
    """
    intervals = split_intervals_by_day(intervals)  # split intervals that span multiple days
    days_dict = defaultdict(list)
    for interval in intervals:
        days_dict[get_day_start(interval.start_datetime)].append(interval)
    return [Day(intervals) for intervals in days_dict.values()]


def get_work_times_at(days, dt_time):
    return [day.get_work_time_at(dt_time) for day in days if day.is_work_day()]


def get_average_work_time_at(days, dt_time):
    work_times_at = get_work_times_at(days, dt_time)
    return sum(work_times_at) / len(work_times_at)


def get_quantile_work_time_at(days, dt_time, quantile):
    worktimes_at = get_work_times_at(days, dt_time)
    return np.quantile(worktimes_at, quantile)


@lru_cache()
def get_days():
    # TODO: This function can be misleading as it does not update
    intervals = get_all_intervals()
    return group_intervals_by_day(intervals)
