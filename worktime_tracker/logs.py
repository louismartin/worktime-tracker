from datetime import datetime
import time
import shutil

from worktime_tracker.constants import WORK_STATES
from worktime_tracker.utils import LOGS_PATH, LAST_CHECK_PATH, reverse_read_lines, seconds_to_human_readable
from worktime_tracker.date_utils import coerce_to_timestamp


_ALL_LOGS = []


def write_last_check(timestamp):
    with LAST_CHECK_PATH.open("w") as f:
        f.write(str(timestamp) + "\n")


def read_last_check_timestamp():
    if not LAST_CHECK_PATH.exists():
        with open(LAST_CHECK_PATH, "w", encoding="utf8") as f:
            f.write("0\n")
    with LAST_CHECK_PATH.open("r") as f:
        return float(f.readline().strip())


def write_log(timestamp, state):
    with LOGS_PATH.open("a") as f:
        f.write(f"{timestamp}\t{state}\n")


def maybe_write_log(timestamp, state):
    # TODO: lock file
    last_log = read_last_log()
    if last_log.state == state:
        return
    write_log(timestamp, state)


def parse_log_line(log_line):
    timestamp, state = log_line.strip().split("\t")
    return Log(timestamp=float(timestamp), state=state)


def reverse_read_logs():
    if not LOGS_PATH.exists():
        LOGS_PATH.parent.mkdir(exist_ok=True)
        write_log(timestamp=0, state="locked")
    for line in reverse_read_lines(LOGS_PATH):
        yield parse_log_line(line)


def get_all_logs():
    # We don't reload all logs each time, just the new ones
    last_log = Log(timestamp=0, state="locked")
    if len(_ALL_LOGS) > 0:
        last_log = _ALL_LOGS[-1]  # Last loaded log
    new_logs = []
    # Read file in reverse to find new logs that are not loaded yet
    for log in reverse_read_logs():
        if log <= last_log:
            break
        new_logs.append(log)
    _ALL_LOGS.extend(new_logs[::-1])
    return _ALL_LOGS.copy()


def get_logs(start_datetime: datetime, end_datetime: datetime):
    # TODO: Merge with get_intervals_between
    end_datetime = min(end_datetime, datetime.now())
    logs = [
        Log(end_datetime.timestamp(), "locked")
    ]  # Add a virtual state at the end of the logs to count the last state
    for log in get_all_logs()[::-1]:  # Read the logs backward
        if log.datetime > end_datetime:
            continue
        if log.datetime <= start_datetime:
            # The first log will be dated at the start timestamp queried
            # Create a new log to prevent mutating the global logs
            log = Log(timestamp=start_datetime.timestamp(), state=log.state)
            break
        logs.append(log)
    return logs[::-1]  # Order the list back to original because we have read the logs backward


def get_all_intervals():
    logs = get_all_logs()
    return convert_logs_to_intervals(logs)

def get_intervals(start_datetime: datetime, end_datetime: datetime):
    logs = get_logs(start_datetime, end_datetime)
    return convert_logs_to_intervals(logs)


def get_intervals_between(intervals, start_datetime, end_datetime):
    """Get intervals between start_datetime and end_datetime"""
    assert start_datetime <= end_datetime
    intervals_between = []
    for interval in intervals:
        if interval.end_datetime < start_datetime or end_datetime < interval.start_datetime:
            # Discard intervals that doe not overlap with the range
            continue
        if interval.start_datetime < start_datetime:
            _, interval = interval.split(start_datetime)
        if end_datetime < interval.end_datetime:
            interval, _ = interval.split(end_datetime)
        intervals_between.append(interval)
    return intervals_between


def read_last_log():
    try:
        return next(reverse_read_logs())
    except StopIteration:
        return None


def read_first_log():
    with open(LOGS_PATH, "r", encoding="utf8") as f:
        try:
            first_line = next(f)
        except StopIteration:
            return None
        return parse_log_line(first_line)


def get_rewritten_history_logs(start_datetime, end_datetime, new_state, logs):
    # TODO: adapt function to use the Log class and datetimes
    start_timestamp = start_datetime.timestamp()
    end_timestamp = end_datetime.timestamp()
    logs = [(log.timestamp, log.state) for log in logs]
    # TODO: Should we compare to datetime.now() instead? Right now if the last log is old, we can't rewrite after it.
    assert end_timestamp < logs[-1][0], "Rewriting the future not allowed"
    # Remove logs that are in the interval to be rewritten
    logs_before = [(timestamp, state) for (timestamp, state) in logs if timestamp <= start_timestamp]
    logs_after = [(timestamp, state) for (timestamp, state) in logs if timestamp > end_timestamp]
    logs_inside = [(timestamp, state) for (timestamp, state) in logs if start_timestamp < timestamp <= end_timestamp]
    if len(logs_inside) > 0:
        # Push back last log inside to be the first of logs after (the rewritten history needs to end on the same
        # state as it was actually recorded)
        logs_after = [(end_timestamp, logs_inside[-1][1])] + logs_after
    else:
        # If there were no states inside, then just take the last log before to have the same state
        logs_after = [(end_timestamp, logs_before[-1][1])] + logs_after
    # Edge cases to not have two identical subsequent states
    if logs_before[-1][1] == new_state:
        # Change the start date to the previous one if it is the same state
        start_timestamp = logs_before[-1][0]
        logs_before = logs_before[:-1]
    if logs_after[0][1] == new_state:
        # Remove first element if it is the same as the one we are going to introduce
        logs_after = logs_after[1:]
    return logs_before + [(start_timestamp, new_state)] + logs_after


def rewrite_history(start_datetime, end_datetime, new_state):
    # Careful, this methods rewrites the entire log file
    shutil.copy(LOGS_PATH, f"{LOGS_PATH}.bck{int(time.time())}")
    logs = get_all_logs()
    # TODO: Rewrite the function to use the Log class
    new_logs = get_rewritten_history_logs(start_datetime, end_datetime, new_state, logs)
    with LOGS_PATH.open("w") as f:
        for timestamp, state in new_logs:
            f.write(f"{timestamp}\t{state}\n")
    _ALL_LOGS[:] = []  # Reset logs


def remove_identical_consecutive_states(logs):
    """Cleans identical consecutive logs which should not change the resulting worktime.

    Should be used to clean the log file."""
    previous_state = None
    new_logs = []
    for timestamp, state in logs:
        if state == previous_state:
            continue
        new_logs.append((timestamp, state))
        previous_state = state
    return new_logs


class Log:
    # TODO: This log abstraction aims at replacing (timestamp, state) tuples
    def __init__(self, timestamp, state):
        self.timestamp = coerce_to_timestamp(timestamp)
        self.state = state

    @property
    def datetime(self):
        return datetime.fromtimestamp(self.timestamp)

    def __repr__(self):
        date_str = self.datetime.strftime("%Y-%m-%d %H:%M:%S")
        return f"Log<date={date_str}, state={self.state}>"

    def __eq__(self, other):
        return self.timestamp == other.timestamp and self.state == other.state

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __le__(self, other):
        return self.timestamp <= other.timestamp

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __ge__(self, other):
        return self.timestamp >= other.timestamp


class Interval:
    def __init__(self, start_log, end_log):
        assert start_log <= end_log
        self.start_log = start_log
        self.end_log = end_log

    @property
    def state(self):
        return self.start_log.state

    @property
    def is_work_interval(self):
        return self.state in WORK_STATES

    @property
    def start_datetime(self):
        return self.start_log.datetime

    @property
    def end_datetime(self):
        return self.end_log.datetime

    @property
    def start_timestamp(self):
        return self.start_log.timestamp

    @property
    def end_timestamp(self):
        return self.end_log.timestamp

    @property
    def duration(self):
        return self.end_timestamp - self.start_timestamp

    @property
    def work_time(self):
        return self.duration if self.is_work_interval else 0

    def split(self, timestamp):
        split_log = Log(timestamp, self.state)
        assert self.start_log <= split_log <= self.end_log
        return Interval(self.start_log, split_log), Interval(split_log, self.end_log)

    def __repr__(self):
        start_str = self.start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        return f"Interval<state:{self.state}, start:{start_str}, duration:{seconds_to_human_readable(self.duration)}>"


def convert_logs_to_intervals(logs):
    return [Interval(start_log, end_log) for start_log, end_log in zip(logs, logs[1:])]
