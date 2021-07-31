import time
import datetime
import re

from tqdm import tqdm

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.utils import seconds_to_human_readable


def parse_time(time_str):
    parts = re.match(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?', time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return datetime.timedelta(**time_params)


def start():
    worktime_tracker = WorktimeTracker()
    while True:
        try:
            worktime_tracker.check_state()
            # Get lines to display
            lines = worktime_tracker.lines()
            # Update menu with new times
            menu = lines[1:][::-1]  # Sort days in chronological order
            work_ratio_last_period = worktime_tracker.get_work_ratio_since_timestamp(time.time() - 3600/2)
            work_time_today = worktime_tracker.get_work_time_from_weekday(worktime_tracker.get_current_weekday())
            title = f'{int(100 * work_ratio_last_period)}% - {seconds_to_human_readable(work_time_today)}'
            print(' - '.join([title] + menu) + '\r', end='')
            time.sleep(30)
        except KeyboardInterrupt:
            duration = parse_time(input('\nInterrupted, press ctrl-c a second time to quit or enter a duration to pause during a certain time (e.g. 2h30).\nDuration: '))
            if duration is not None:
                print(f'Pausing for {duration}.')
                for i in tqdm(range(duration.seconds)):
                    time.sleep(1)

