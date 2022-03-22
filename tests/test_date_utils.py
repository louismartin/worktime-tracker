from datetime import datetime, date
from worktime_tracker.date_utils import parse_time, is_datetime_in_date


def test_parse_time():
    assert parse_time("30m").seconds == 30 * 60
    assert parse_time("1h30m").seconds == 90 * 60
    assert parse_time("2h").seconds == 120 * 60


def test_is_datetime_in_date():
    assert is_datetime_in_date(datetime(2022, 3, 19, 9), date(2022, 3, 19))
    assert is_datetime_in_date(datetime(2022, 3, 20, 2), date(2022, 3, 19))
    # Considered previous day
    assert not is_datetime_in_date(datetime(2022, 3, 19, 3), date(2022, 3, 19))
    assert is_datetime_in_date(datetime(2022, 3, 19, 3), date(2022, 3, 18))
