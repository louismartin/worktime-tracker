import time
import shutil
import datetime

from worktime_tracker.constants import STATES_TYPE, LOGS_PATH, LAST_CHECK_PATH
from worktime_tracker.utils import reverse_read_lines
from worktime_tracker.date_utils import coerce_to_timestamp


class Log:
    """Represents a log entry at a single point of time, basically containing a timestamp and a state.
    It is supposed to match the format of the logs file.
    """
    def __init__(self, timestamp: float, state: STATES_TYPE) -> None:
        self.timestamp = coerce_to_timestamp(timestamp)
        self.state = state

    @property
    def datetime(self) -> datetime.datetime:
        return datetime.datetime.fromtimestamp(self.timestamp)

    def __repr__(self) -> str:
        date_str = self.datetime.strftime("%Y-%m-%d %H:%M:%S")
        return f"Log<date={date_str}, state={self.state}>"

    def __eq__(self, other) -> bool:
        return self.timestamp == other.timestamp and self.state == other.state

    def __lt__(self, other) -> bool:
        return self.timestamp < other.timestamp

    def __le__(self, other) -> bool:
        return self.timestamp <= other.timestamp

    def __gt__(self, other) -> bool:
        return self.timestamp > other.timestamp

    def __ge__(self, other) -> bool:
        return self.timestamp >= other.timestamp


def write_last_check(timestamp: float) -> None:
    with LAST_CHECK_PATH.open("w") as f:
        f.write(str(timestamp) + "\n")


def read_last_check_timestamp() -> float:
    if not LAST_CHECK_PATH.exists():
        with open(LAST_CHECK_PATH, "w", encoding="utf8") as f:
            f.write("0\n")
    with LAST_CHECK_PATH.open("r") as f:
        return float(f.readline().strip())


def write_log(log: Log) -> None:
    with LOGS_PATH.open("a") as f:
        f.write(f"{log.timestamp}\t{log.state}\n")


def maybe_write_log(log: Log):
    # TODO: lock file
    last_log = read_last_log()
    if last_log.state == log.state:
        return
    write_log(log)


def parse_log_line(log_line: str) -> Log:
    timestamp, state = log_line.strip().split("\t")
    return Log(timestamp=float(timestamp), state=state)


def reverse_read_logs() -> list[Log]:
    if not LOGS_PATH.exists():
        LOGS_PATH.parent.mkdir(exist_ok=True)
        write_log(Log(timestamp=0, state="locked"))
    for line in reverse_read_lines(LOGS_PATH):
        yield parse_log_line(line)


def read_last_log() -> Log:
    try:
        return next(reverse_read_logs())
    except StopIteration:
        return None


def read_first_log() -> Log:
    with open(LOGS_PATH, "r", encoding="utf8") as f:
        try:
            first_line = next(f)
        except StopIteration:
            return None
        return parse_log_line(first_line)


def get_rewritten_history_logs(logs: list[Log], start_datetime: datetime.datetime, end_datetime: datetime.datetime, new_state: STATES_TYPE) -> list[Log]:
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


def rewrite_history(start_datetime: datetime.datetime, end_datetime: datetime.datetime, new_state: STATES_TYPE) -> None:
    raise NotImplementedError  # TODO: Reimplement
    # # Careful, this methods rewrites the entire log file
    # backup_dir = LOGS_PATH.parent / "backup"
    # backup_dir.mkdir(exist_ok=True)
    # shutil.copy(LOGS_PATH, backup_dir / f"{LOGS_PATH.name}.bck{int(time.time())}")
    # logs = get_all_logs()
    # logs += [Log(time.time(), "locked")]  # So that we take the last interval into account
    # # TODO: Rewrite the function to use the Log class
    # new_logs = get_rewritten_history_logs(start_datetime, end_datetime, new_state, logs)
    # with LOGS_PATH.open("w") as f:
    #     for timestamp, state in new_logs:
    #         f.write(f"{timestamp}\t{state}\n")
    # _ALL_LOGS[:] = []  # Reset logs


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

