import time
from datetime import datetime, timedelta
from worktime_tracker.constants import DAY_START_HOUR


WEEKDAYS = [
    'Sunday',
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
]


def get_day_start(dt):
    return (
        (dt - timedelta(hours=DAY_START_HOUR))
        .replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def get_current_day_start():
    return (
        (datetime.now() - timedelta(hours=DAY_START_HOUR))
        .replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)
        .timestamp()
    )


def get_current_day_end():
    return get_current_day_start() + timedelta(days=1).total_seconds()


def get_current_weekday():
    # Add +2 to start the week on saturday
    return ((datetime.now() - timedelta(hours=DAY_START_HOUR)).weekday() + WEEKDAYS.index('Monday')) % 7


def get_week_start():
    delta = timedelta(days=get_current_weekday(), hours=DAY_START_HOUR)
    return (datetime.now() - delta).replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0).timestamp()


def is_this_week(query_timestamp):
    assert query_timestamp <= time.time()
    return query_timestamp >= get_week_start()


def get_timestamp_weekday(timestamp):
    query_datetime = datetime.fromtimestamp(timestamp)
    return (query_datetime + timedelta(hours=-DAY_START_HOUR)).weekday()


def get_weekday_start_and_end(weekday):
    current_weekday = get_current_weekday()
    assert weekday <= current_weekday, 'Cannot query future weekday'
    day_offset = current_weekday - weekday
    weekday_start = get_current_day_start() - timedelta(days=day_offset).total_seconds()
    weekday_end = get_current_day_end() - timedelta(days=day_offset).total_seconds()
    return weekday_start, weekday_end
