import time
import re
from datetime import datetime, timedelta


DAY_START_HOUR = 7  # Hour at which the day starts
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


def get_date(dt):
    return (dt - timedelta(hours=DAY_START_HOUR)).date()


def get_day_start(date_like=None):
    if date_like is None:
        date_like = datetime.now()
    if isinstance(date_like, datetime):
        date_like = get_date(date_like)
    return datetime(date_like.year, date_like.month, date_like.day, DAY_START_HOUR)


def get_day_end(date_like=None):
    return get_day_start(date_like) + timedelta(days=1)


def get_current_day_start():  # Just an alias
    return get_day_start()


def get_current_day_end():  # Just an alias
    return get_day_end()


def get_weekday_idx_from_datetime(dt):
    weekday = (dt - timedelta(hours=DAY_START_HOUR)).weekday()
    offset = WEEKDAYS.index("Monday")
    return (weekday + offset) % 7


def get_current_weekday():
    return get_weekday_idx_from_datetime(datetime.now())


def get_week_start():
    delta = timedelta(days=get_current_weekday(), hours=DAY_START_HOUR)
    return (datetime.now() - delta).replace(hour=DAY_START_HOUR, minute=0, second=0, microsecond=0)


def get_month_start():
    return (datetime.now() - timedelta(hours=DAY_START_HOUR)).replace(
        day=1, hour=DAY_START_HOUR, minute=0, second=0, microsecond=0
    )


def get_year_start():
    return (datetime.now() - timedelta(hours=DAY_START_HOUR)).replace(
        month=1, day=1, hour=DAY_START_HOUR, minute=0, second=0, microsecond=0
    )


def is_this_week(query_timestamp):
    assert query_timestamp <= time.time()
    return query_timestamp >= get_week_start().timestamp()


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


def is_datetime_in_date(dt, d):
    return get_date(dt) == d
