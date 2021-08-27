from collections import defaultdict
from datetime import datetime, timedelta
import shutil
import time

from worktime_tracker.utils import LOGS_PATH, LAST_CHECK_PATH, reverse_read_lines, seconds_to_human_readable
from worktime_tracker.spaces import get_state


ALL_LOGS = []


def write_last_check(timestamp):
    with LAST_CHECK_PATH.open('w') as f:
        f.write(str(timestamp) + '\n')


def read_last_check_timestamp():
    if not LAST_CHECK_PATH.exists():
        with open(LAST_CHECK_PATH, 'w') as f:
            f.write('0\n')
    with LAST_CHECK_PATH.open('r') as f:
        return float(f.readline().strip())


def maybe_fix_unfinished_work_state():
    '''If the app was killed during a work state, it will count everything from this moment as work.
    We want to fix it if this is the case'''
    timestamp = time.time()
    last_check_timestamp = read_last_check_timestamp()
    last_timestamp, last_state = read_last_log()
    if timestamp - last_check_timestamp < 60:
        return
    if last_state not in WorktimeTracker.work_states:
        return
    write_last_check(timestamp)
    maybe_write_log(last_check_timestamp + 1, 'locked')


def write_log(timestamp, state):
    with LOGS_PATH.open('a') as f:
        f.write(f'{timestamp}\t{state}\n')


def maybe_write_log(timestamp, state):
    # TODO: lock file
    _, last_state = read_last_log()
    if last_state == state:
        return
    write_log(timestamp, state)


def parse_log_line(log_line):
    timestamp, state = log_line.strip().split('\t')
    return float(timestamp), state


def reverse_read_logs():
    if not LOGS_PATH.exists():
        LOGS_PATH.parent.mkdir(exist_ok=True)
        write_log(timestamp=0, state='locked')
    for line in reverse_read_lines(LOGS_PATH):
        yield parse_log_line(line)


def get_all_logs():
    # We don't reload all logs each time, just the new ones
    global ALL_LOGS
    last_timestamp = 0
    if len(ALL_LOGS) > 0:
        last_timestamp, _ = ALL_LOGS[-1]  # Last loaded log
    new_logs = []
    # Read file in reverse to find new logs that are not loaded yet
    for timestamp, state in reverse_read_logs():
        if timestamp <= last_timestamp:
            break
        new_logs.append((timestamp, state))
    ALL_LOGS.extend(new_logs[::-1])
    return ALL_LOGS.copy()


def get_logs(start_timestamp, end_timestamp):
    end_timestamp = min(end_timestamp, time.time())
    logs = [(end_timestamp, 'locked')]  # Add a virtual state at the end of the logs to count the last state
    for timestamp, state in get_all_logs()[::-1]:  # Read the logs backward
        if timestamp > end_timestamp:
            continue
        if timestamp < start_timestamp:
            logs.append((start_timestamp, state))  # The first log will be dated at the start timestamp queried
            break
        logs.append((timestamp, state))
    return logs[::-1]  # Order the list back to original because we have read the logs backward


def read_last_log():
    try:
        return next(reverse_read_logs())
    except StopIteration:
        return None


def read_first_log():
    with open(LOGS_PATH, 'r') as f:
        try:
            first_line = next(f)
        except StopIteration:
            return None
        return parse_log_line(first_line)


def get_rewritten_history_logs(start_timestamp, end_timestamp, new_state, logs):
    assert end_timestamp < logs[-1][0], 'Rewriting the future not allowed'
    # Remove logs that are in the interval to be rewritten
    logs_before = [(timestamp, state) for (timestamp, state) in logs
                   if timestamp <= start_timestamp]
    logs_after = [(timestamp, state) for (timestamp, state) in logs
                  if timestamp > end_timestamp]
    logs_inside = [(timestamp, state) for (timestamp, state) in logs
                   if start_timestamp < timestamp and timestamp <= end_timestamp]
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


def rewrite_history(start_timestamp, end_timestamp, new_state):
    # Careful, this methods rewrites the entire log file
    shutil.copy(LOGS_PATH, f'{LOGS_PATH}.bck{int(time.time())}')
    with LOGS_PATH.open('r') as f:
        logs = get_logs(start_timestamp=0, end_timestamp=time.time())
    new_logs = get_rewritten_history_logs(start_timestamp, end_timestamp, new_state, logs)
    with LOGS_PATH.open('w') as f:
        for timestamp, state in new_logs:
            f.write(f'{timestamp}\t{state}\n')
    global ALL_LOGS
    ALL_LOGS[:] = []  # Reset logs


def get_cum_times_per_state(start_timestamp, end_timestamp):
    assert start_timestamp < end_timestamp
    logs = get_logs(start_timestamp, end_timestamp)
    cum_times_per_state = defaultdict(float)
    current_state_start_timestamp, current_state = logs[0]
    for new_timestamp, new_state in logs[1:]:
        if new_state == current_state:
            continue
        cum_times_per_state[current_state] += (new_timestamp - max(current_state_start_timestamp, start_timestamp))
        current_state = new_state
        current_state_start_timestamp = new_timestamp
    return cum_times_per_state


def get_work_time(start_timestamp, end_timestamp):
    cum_times = get_cum_times_per_state(start_timestamp, end_timestamp)
    return sum(cum_times[state] for state in WorktimeTracker.work_states)


class WorktimeTracker:

    states = ['work', 'personal', 'locked']
    work_states = ['work']
    targets = [
        0,  # Sunday
        6.25 * 3600,  # Monday
        6.25 * 3600,  # Tuesday
        6.25 * 3600,  # Wednesday
        6.25 * 3600,  # Thursday
        5 * 3600,  # Friday
        0,  # Saturday
    ]
    weekdays = [
            'Sunday',
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
    ]
    day_start_hour = 7  # Hour at which the day starts

    def __init__(self, read_only=False):
        maybe_fix_unfinished_work_state()
        self.read_only = read_only

    @staticmethod
    def is_work_state(state):
        return state in WorktimeTracker.work_states

    @property
    def current_state(self):
        return read_last_log()[1]

    def get_work_ratio_since_timestamp(self, start_timestamp):
        end_timestamp = time.time()
        work_time = get_work_time(start_timestamp, end_timestamp)
        return work_time / (end_timestamp - start_timestamp)

    @staticmethod
    def get_current_weekday():
        # Add +2 to start the week on saturday
        return ((datetime.today() - timedelta(hours=WorktimeTracker.day_start_hour)).weekday() + WorktimeTracker.weekdays.index('Monday')) % 7

    @staticmethod
    def get_current_day_start():
        return (datetime.today() - timedelta(hours=WorktimeTracker.day_start_hour)).replace(
            hour=WorktimeTracker.day_start_hour,
            minute=0,
            second=0,
            microsecond=0
        ).timestamp()

    @staticmethod
    def get_current_day_end():
        return WorktimeTracker.get_current_day_start() + timedelta(days=1).total_seconds()

    @staticmethod
    def get_week_start():
        delta = timedelta(days=WorktimeTracker.get_current_weekday(), hours=WorktimeTracker.day_start_hour)
        return (datetime.today() - delta).replace(hour=WorktimeTracker.day_start_hour,
                                                  minute=0,
                                                  second=0,
                                                  microsecond=0).timestamp()

    @staticmethod
    def is_this_week(query_timestamp):
        assert query_timestamp <= time.time()
        return query_timestamp >= WorktimeTracker.get_week_start()

    @staticmethod
    def get_timestamp_weekday(timestamp):
        query_datetime = datetime.fromtimestamp(timestamp)
        return (query_datetime + timedelta(hours=-WorktimeTracker.day_start_hour)).weekday()

    @staticmethod
    def get_weekday_timestamps(weekday):
        current_weekday = WorktimeTracker.get_current_weekday()
        assert weekday <= current_weekday, 'Cannot query future weekday'
        day_offset = current_weekday - weekday
        weekday_start = WorktimeTracker.get_current_day_start() - timedelta(days=day_offset).total_seconds()
        weekday_end = WorktimeTracker.get_current_day_end() - timedelta(days=day_offset).total_seconds()
        return weekday_start, weekday_end

    def get_work_time_from_weekday(self, weekday):
        weekday_start, weekday_end = WorktimeTracker.get_weekday_timestamps(weekday)
        return get_work_time(weekday_start, weekday_end)

    def maybe_append_and_write_log(self, timestamp, state):
        if self.read_only:
            False
        maybe_write_log(timestamp, state)

    def check_state(self):
        '''Checks the current state and update the logs. Returns a boolean of whether the state changed or not'''
        # TODO: We should split the writing logic and the state checking logic
        _, last_state = read_last_log()
        state = get_state()
        timestamp = time.time()
        write_last_check(timestamp)
        self.maybe_append_and_write_log(timestamp, state)
        return state != last_state

    def lines(self):
        '''Nicely formatted lines for displaying to the user'''
        def weekday_text(weekday_idx):
            weekday = WorktimeTracker.weekdays[weekday_idx]
            work_time = self.get_work_time_from_weekday(weekday_idx)
            target = WorktimeTracker.targets[weekday_idx]
            ratio = work_time / target if target != 0 else 1
            return f'{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(work_time)})'

        def total_worktime_text():
            work_time = sum([self.get_work_time_from_weekday(weekday_idx)
                             for weekday_idx in range(WorktimeTracker.get_current_weekday())])
            target = sum([WorktimeTracker.targets[weekday_idx]
                          for weekday_idx in range(WorktimeTracker.get_current_weekday())])
            return f'Week overtime: {seconds_to_human_readable(work_time - target)}'

        lines = [weekday_text(weekday_idx) for weekday_idx in range(WorktimeTracker.get_current_weekday() + 1)][::-1]
        lines += [total_worktime_text()]
        return lines
