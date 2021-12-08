from collections import defaultdict
import time

from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.spaces import get_state
from worktime_tracker.constants import WORK_STATES
from worktime_tracker.date_utils import get_weekday_start_and_end, WEEKDAYS, get_current_weekday
from worktime_tracker.logs import get_logs, read_last_log, maybe_write_log, write_last_check, read_last_check_timestamp


def get_cum_times_per_state(start_timestamp, end_timestamp):
    assert start_timestamp < end_timestamp
    logs = get_logs(start_timestamp, end_timestamp)
    cum_times_per_state = defaultdict(float)
    current_state_start_timestamp, current_state = logs[0]
    for new_timestamp, new_state in logs[1:]:
        if new_state == current_state:
            continue
        cum_times_per_state[current_state] += new_timestamp - max(current_state_start_timestamp, start_timestamp)
        current_state = new_state
        current_state_start_timestamp = new_timestamp
    return cum_times_per_state


def get_work_time(start_timestamp, end_timestamp):
    cum_times = get_cum_times_per_state(start_timestamp, end_timestamp)
    return sum(cum_times[state] for state in WORK_STATES)


def maybe_fix_unfinished_work_state():
    '''If the app was killed during a work state, it will count everything from this moment as work.
    We want to fix it if this is the case'''
    timestamp = time.time()
    last_check_timestamp = read_last_check_timestamp()
    _, last_state = read_last_log()
    if timestamp - last_check_timestamp < 60:
        return
    if last_state not in WORK_STATES:
        return
    write_last_check(timestamp)
    maybe_write_log(last_check_timestamp + 1, 'locked')


class WorktimeTracker:

    targets = [
        0,  # Sunday
        6.25 * 3600,  # Monday
        6.25 * 3600,  # Tuesday
        6.25 * 3600,  # Wednesday
        6.25 * 3600,  # Thursday
        5 * 3600,  # Friday
        0,  # Saturday
    ]

    def __init__(self, read_only=False):
        maybe_fix_unfinished_work_state()
        self.read_only = read_only

    @staticmethod
    def is_work_state(state):
        return state in WORK_STATES

    @property
    def current_state(self):
        return read_last_log()[1]

    # TODO: Move all these static methods to functions?
    @staticmethod
    def get_work_ratio_since_timestamp(start_timestamp):
        end_timestamp = time.time()
        work_time = get_work_time(start_timestamp, end_timestamp)
        return work_time / (end_timestamp - start_timestamp)

    @staticmethod
    def get_work_time_from_weekday(weekday):
        weekday_start, weekday_end = get_weekday_start_and_end(weekday)
        return get_work_time(weekday_start, weekday_end)

    def maybe_append_and_write_log(self, timestamp, state):
        if self.read_only:
            return
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
            weekday = WEEKDAYS[weekday_idx]
            work_time = self.get_work_time_from_weekday(weekday_idx)
            target = WorktimeTracker.targets[weekday_idx]
            ratio = work_time / target if target != 0 else 1
            return f'{weekday[:3]}: {int(100 * ratio)}% ({seconds_to_human_readable(work_time)})'

        def total_worktime_text():
            work_time = sum(
                [self.get_work_time_from_weekday(weekday_idx) for weekday_idx in range(get_current_weekday())]
            )
            target = sum([WorktimeTracker.targets[weekday_idx] for weekday_idx in range(get_current_weekday())])
            return f'Week overtime: {seconds_to_human_readable(work_time - target)}'

        lines = [weekday_text(weekday_idx) for weekday_idx in range(get_current_weekday() + 1)][::-1]
        lines += [total_worktime_text()]
        return lines
