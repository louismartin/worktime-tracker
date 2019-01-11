from collections import defaultdict
from datetime import datetime, timedelta
import time

from worktime_tracker.utils import LOGS_PATH, LAST_CHECK_PATH, get_state, reverse_read_line, seconds_to_human_readable


def write_last_check(timestamp):
    with LAST_CHECK_PATH.open('w') as f:
        f.write(str(timestamp) + '\n')


def read_last_check():
    with LAST_CHECK_PATH.open('r') as f:
        return float(f.readline().strip())


def write_log(timestamp, state):
    # TODO: lock file
    with LOGS_PATH.open('a') as f:
        # TODO: Check that newly written state is different from previous one
        f.write(f'{timestamp}\t{state}\n')


def read_last_log():
    try:
        last_line = next(reverse_read_line(LOGS_PATH))
    except StopIteration:
        return None
    timestamp, state = last_line.strip().split('\t')
    return float(timestamp), state


class WorktimeTracker:

    states = ['work', 'email', 'leisure', 'idle']
    work_states = ['work', 'email']
    targets = {
        0: 6 * 3600,  # Monday
        1: 6 * 3600,  # Tuesday
        2: 6 * 3600,  # Wednesday
        3: 6 * 3600,  # Thursday
        4: 5 * 3600,  # Friday
        5: 0,  # Saturday
        6: 0,  # Sunday
    }
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_start_hour = 7  # Hour at which the day starts

    def __init__(self, read_only=False):
        self.read_only = read_only
        LOGS_PATH.touch()  # Creates file if it does not exist
        self.logs = []
        self.load_logs()

    @property
    def cum_times(self):
        cum_times = defaultdict(float)
        logs = self.logs.copy()
        if logs[-1][1] != 'idle':
            logs += [(time.time(), 'idle')]  # Add a virtual state at the end to count the last interval
        for (start_timestamp, state), (end_timestamp, next_state) in zip(logs[:-1], logs[1:]):
            assert state != next_state
            weekday = WorktimeTracker.get_timestamp_weekday(start_timestamp)
            cum_times[weekday, state] += (end_timestamp - start_timestamp)
        return cum_times

    @staticmethod
    def current_weekday():
        return (datetime.today() - timedelta(hours=7)).weekday()

    @staticmethod
    def is_this_week(timestamp):
        query_datetime = datetime.fromtimestamp(timestamp)
        current_datetime = datetime.today()
        assert query_datetime <= current_datetime
        week_start = (current_datetime + timedelta(days=-current_datetime.weekday()))
        week_start = week_start.replace(hour=WorktimeTracker.day_start_hour, minute=0)
        return query_datetime >= week_start

    @staticmethod
    def get_timestamp_weekday(timestamp):
        query_datetime = datetime.fromtimestamp(timestamp)
        return (query_datetime + timedelta(hours=-WorktimeTracker.day_start_hour)).weekday()

    def get_work_time_from_weekday(self, weekday):
        assert weekday in range(7)
        return sum([self.cum_times[weekday, state] for state in WorktimeTracker.work_states])

    def append_and_write_log(self, timestamp, state):
        self.logs.append((timestamp, state))
        if self.read_only:
            return
        write_log(timestamp, state)

    @staticmethod
    def get_this_weeks_logs():
        logs = []
        for line in reverse_read_line(LOGS_PATH):
            timestamp, state = line.strip().split('\t')
            if not WorktimeTracker.is_this_week(float(timestamp)):
                break
            logs.append((float(timestamp), state))
        return logs[::-1]  # We read the logs backward

    def load_logs(self):
        # TODO: If the program was killed two hours ago on work state, then it will probably count two hours of work
        last_log = read_last_log()
        if last_log is None or not WorktimeTracker.is_this_week(float(last_log[0])):
            if not self.read_only:
                write_log(time.time(), 'idle')
        if last_log[1] != 'idle':
            # Add a log pretending the computer was idle at the last time the state was checked
            if not self.read_only:
                write_log(read_last_check(), 'idle')
        self.logs = WorktimeTracker.get_this_weeks_logs()

    def check_state(self):
        '''Checks the current state and update the logs. Returns a boolean of whether the state changed or not'''
        state = get_state()
        timestamp = time.time()
        write_last_check(timestamp)
        last_timestamp, last_state = self.logs[-1]
        if state != last_state:
            self.append_and_write_log(timestamp, state)
            return True
        return False

    def lines(self):
        '''Nicely formatted lines for displaying to the user'''
        def weekday_text(weekday_idx):
            weekday = WorktimeTracker.weekdays[weekday_idx]
            work_time = self.get_work_time_from_weekday(weekday_idx)
            target = WorktimeTracker.targets[weekday_idx]
            ratio = work_time / target if target != 0 else 1
            return f'{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(work_time)})'

        return [weekday_text(weekday_idx) for weekday_idx in range(WorktimeTracker.current_weekday() + 1)][::-1]
