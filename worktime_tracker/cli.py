import time

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.tools import pause, get_ghost_plot, rewrite_history_prompt, plot_productivity
from worktime_tracker.constants import REFRESH_RATE


def start():
    worktime_tracker = WorktimeTracker()
    while True:
        try:
            worktime_tracker.check_state()
            summaries = worktime_tracker.get_week_summaries()
            print(" - ".join([get_ghost_plot(length=50)] + summaries) + "\r", end="")
            time.sleep(REFRESH_RATE)
        except KeyboardInterrupt:
            options_to_methods = {
                "0. Pause for a certain duration": pause,
                "1. Plot productivity": plot_productivity,
                "2. Rewrite history": rewrite_history_prompt,
            }
            options_str = "\n".join(options_to_methods.keys())
            option_index = int(
                input(
                    "\nInterrupted, press ctrl-c a second time to quit or select one of the following options:"
                    f"\n\n{options_str}\n\nOption: "
                )
            )
            method = list(options_to_methods.values())[option_index]
            method()
