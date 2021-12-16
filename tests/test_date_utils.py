from worktime_tracker.date_utils import parse_time


def test_parse_time():
    parse_time("30m").seconds == 30*60
    parse_time("1h30m").seconds == 90*60
    parse_time("2h").seconds == 120*60