import time

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.utils import seconds_to_human_readable


def start():
    while True:
        worktime_tracker = WorktimeTracker()
        worktime_tracker.check_state()
        # Get lines to display
        lines = worktime_tracker.lines()
        # Update menu with new times
        menu = lines[1:][::-1]  # Sort days in chronological order
        work_ratio_last_period = worktime_tracker.get_work_ratio_since_timestamp(time.time() - 3600/2)
        work_time_today = worktime_tracker.get_work_time_from_weekday(worktime_tracker.get_current_weekday())
        title = f'{int(100 * work_ratio_last_period)}% - {seconds_to_human_readable(work_time_today)}'
        print(' - '.join([title] + menu) + '\r', end='')
        time.sleep(10)
