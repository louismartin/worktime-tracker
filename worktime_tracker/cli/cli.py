import time
import datetime
import re
import subprocess

from tqdm import tqdm

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.date_utils import get_current_weekday
from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.tools import rewrite_history_prompt, download_productivity_plot


def parse_time(time_str):
    parts = re.match(r"((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?", time_str)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}
    for name, param in parts.items():
        if param:
            time_params[name] = int(param)
    return datetime.timedelta(**time_params)


def pause():
    duration = parse_time(input("Enter a duration to pause during a certain time (e.g. 2h30).\nDuration: "))
    if duration is not None:
        print(f"Pausing for {duration}.")
        for i in tqdm(range(duration.seconds)):
            time.sleep(1)


def plot_productivity():
    productivity_plot_path = download_productivity_plot()
    # TODO: Only works on macos for now
    subprocess.run(["open", productivity_plot_path])


def start():
    worktime_tracker = WorktimeTracker()
    while True:
        try:
            worktime_tracker.check_state()
            # Get lines to display
            lines = worktime_tracker.lines()
            # Update menu with new times
            menu = lines[1:][::-1]  # Sort days in chronological order
            work_ratio_last_period = worktime_tracker.get_work_ratio_since_timestamp(time.time() - 3600 / 2)
            work_time_today = worktime_tracker.get_work_time_from_weekday(get_current_weekday())
            title = f"{int(100 * work_ratio_last_period)}% - {seconds_to_human_readable(work_time_today)}"
            print(" - ".join([title] + menu) + "\r", end="")
            time.sleep(30)
        except KeyboardInterrupt:
            options_to_methods = {
                "0. Pause for a certain duration": pause,
                "1. Plot productivity": plot_productivity,
                "2. Rewrite history": rewrite_history_prompt,
            }
            options_str = "\n".join(options_to_methods.keys())
            option_index = int(
                input(
                    f"\nInterrupted, press ctrl-c a second time to quit or select one of the following options:\n\n{options_str}\n\nOption: "
                )
            )
            method = list(options_to_methods.values())[option_index]
            method()
