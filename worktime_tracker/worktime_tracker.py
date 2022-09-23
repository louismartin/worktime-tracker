import time
from datetime import datetime
from datetime import timedelta
from functools import lru_cache

from worktime_tracker.config import Config
from worktime_tracker.constants import DONT_COUNT_DAYS_PATH, WORK_STATES, DAYS_OFF_PATH
from worktime_tracker.date_utils import (
    WEEKDAYS,
    coerce_to_datetime,
    get_current_weekday,
    get_day_start,
    get_month_start,
    get_week_start,
    get_weekday_idx_from_datetime,
    get_weekday_start_and_end,
    get_year_start,
)
from worktime_tracker.logs import Log, maybe_write_log, read_last_check_timestamp, read_last_log, write_last_check
from worktime_tracker.spaces import get_state
from worktime_tracker.utils import seconds_to_human_readable, yield_lines_without_comments
from worktime_tracker.history import History


@lru_cache
def get_days_off():
    """Days off are used to set the target of days off to 0.

    Returns a dict of dates to day off proportion (e.g. 1 means full day off, 0.5 half a day off, 0 not a day off)
    """
    days_off = {}
    if not DAYS_OFF_PATH.exists():
        return days_off
    for line in yield_lines_without_comments(DAYS_OFF_PATH):
        # Parse date in the format 2022-03-19
        date, proportion, *_ = line.split("\t")
        days_off[datetime.strptime(date, "%Y-%m-%d").date()] = float(proportion)
    return days_off


@lru_cache
def get_dont_count_days():
    """``Don't count" days are used to remove some days from the worktime tracker entirely (e.g. conference days so that they don't count as undertime)."""
    # TODO: Not used yet
    dont_count_days = []
    if not DONT_COUNT_DAYS_PATH.exists():
        return dont_count_days
    for date in yield_lines_without_comments(DONT_COUNT_DAYS_PATH):
        # Parse date in the format 2022-03-19
        dont_count_days.append(datetime.strptime(date, "%Y-%m-%d").date())
    return dont_count_days


def get_worktime_between(start_datetime: datetime, end_datetime: datetime):
    # TODO: Deprecate this method and use History directly
    assert start_datetime <= end_datetime
    history = History()  # Singleton
    return history.get_worktime_between(start_datetime, end_datetime, dont_count_days=get_dont_count_days())


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


def get_work_ratio_since_timestamp(start_timestamp):
    end_datetime = datetime.now()
    worktime = get_worktime_between(start_datetime=coerce_to_datetime(start_timestamp), end_datetime=datetime.now())
    return worktime / (end_datetime.timestamp() - start_timestamp)


def get_worktime_from_weekday(weekday):
    weekday_start, weekday_end = get_weekday_start_and_end(weekday)
    return get_worktime_between(weekday_start, weekday_end)


def get_todays_worktime():
    return get_worktime_from_weekday(get_current_weekday())


def get_worktime_target_from_datetime(dt):
    if dt in get_dont_count_days():
        return 0
    if dt.date() not in [day.date for day in History().days if day.worktime > 0]:
        # TODO: If that's too slow we can only compare to the oldest day in the history
        # Don't consider days that where not worked
        return 0
    # 1 means full day off, 0.5 half a day off, 0 not a day off
    dont_count_proportion = get_days_off()
    dont_count_proportion = dont_count_proportion.get(dt.date(), 0)
    return WorktimeTracker.targets[get_weekday_idx_from_datetime(dt)] * (1 - dont_count_proportion)


def get_worktime_target_between(start_datetime, end_datetime):
    start_datetime = get_day_start(start_datetime)
    end_datetime = get_day_start(end_datetime)  # Does not include the target of the last day
    day_interval = (end_datetime - start_datetime).days
    return sum(get_worktime_target_from_datetime(start_datetime + timedelta(days=i)) for i in range(day_interval))


def get_overtime_between(start_datetime, end_datetime):
    worktime = get_worktime_between(start_datetime, end_datetime)
    target = get_worktime_target_between(start_datetime, end_datetime)
    return worktime - target


class WorktimeTracker:
    # TODO: We should remove this class entirely

    targets = [
        0,  # Sunday
        6.25 * 3600,  # Monday
        6.25 * 3600,  # Tuesday
        6.25 * 3600,  # Wednesday
        6.25 * 3600,  # Thursday
        5 * 3600,  # Friday
        0,  # Saturday
    ]

    def __init__(self):
        maybe_fix_unfinished_work_state()

    @staticmethod
    def is_work_state(state):
        return state in WORK_STATES

    @property
    def current_state(self):
        return read_last_log().state

    def check_state(self):
        """Checks the current state and update the logs. Returns a boolean of whether the state changed or not"""
        # TODO: We should split the writing logic and the state checking logic
        last_log = read_last_log()
        timestamp = time.time()
        write_last_check(timestamp)
        state = get_state()
        maybe_write_log(Log(timestamp, state))
        return state != last_log.state

    def get_weekday_summary(self, weekday_idx):
        weekday = WEEKDAYS[weekday_idx]
        worktime = get_worktime_from_weekday(weekday_idx)
        target = WorktimeTracker.targets[weekday_idx]
        ratio = worktime / target if target != 0 else 1
        return f"{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(worktime)})"

    def get_week_overtime_summary(self):
        overtime = get_overtime_between(get_week_start(), get_day_start())
        return f"Week overtime: {seconds_to_human_readable(overtime)}"

    def get_month_overtime_summary(self):
        overtime = get_overtime_between(get_month_start(), get_day_start())
        return f"Month overtime: {seconds_to_human_readable(overtime)}"

    def get_year_overtime_summary(self):
        overtime = get_overtime_between(get_year_start(), get_day_start())
        return f"Year overtime: {seconds_to_human_readable(overtime)}"

    def get_instant_summary(self):
        work_ratio_last_period = get_work_ratio_since_timestamp(time.time() - 3600 / 2)
        instant_summary = f"{work_ratio_last_period:.0%}"
        if Config().show_day_worktime:
            worktime_today = get_worktime_from_weekday(get_current_weekday())
            instant_summary = f"{instant_summary} - {seconds_to_human_readable(worktime_today)}"
        return instant_summary

    def get_week_summaries(self):
        """Nicely formatted day summaries for displaying to the user"""
        summaries = [self.get_weekday_summary(weekday_idx) for weekday_idx in range(get_current_weekday() + 1)][::-1]
        summaries += [
            self.get_year_overtime_summary(),
            self.get_month_overtime_summary(),
            self.get_week_overtime_summary(),
        ]
        return summaries
