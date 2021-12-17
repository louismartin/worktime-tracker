import time
import re
from datetime import datetime, timedelta

from worktime_tracker.constants import DAY_START_HOUR


WEEKDAYS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def coerce_to_datetime(datetime_like):
    if isinstance(datetime_like, datetime):
        return datetime_like
    return datetime.fromtimestamp(datetime_like)


def coerce_to_timestamp(timestamp_like):
    if isinstance(timestamp_like, (int, float)):
        return timestamp_like
    return timestamp_like.timestamp()


def get_day_start(dt):
    return (dt - timedelta(hours=DAY_START_HOUR)).replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)


def get_day_end(dt):
    return get_day_start(dt) + timedelta(days=1)


def get_current_day_start():
    return get_day_start(datetime.now())


def get_current_day_end():
    return get_day_end(datetime.now())


def get_current_weekday():
    # Add +2 to start the week on saturday
    return ((datetime.now() - timedelta(hours=DAY_START_HOUR)).weekday() + WEEKDAYS.index("Monday")) % 7


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
    assert weekday <= current_weekday, "Cannot query future weekday"
    day_offset = current_weekday - weekday
    weekday_start = get_current_day_start() - timedelta(days=day_offset)
    weekday_end = get_current_day_end() - timedelta(days=day_offset)
    return weekday_start, weekday_end


def parse_time(time_str):
    parts = re.match(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?", time_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)
