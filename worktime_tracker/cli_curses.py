import time
import curses

from worktime_tracker.constants import REFRESH_RATE
from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.tools import get_ghost_plot, rewrite_history_prompt, plot_productivity


def curses_app(stdscr):
    # Clear screen
    stdscr.clear()
    worktime_tracker = WorktimeTracker()
    while True:
        try:
            worktime_tracker.check_state()
            summaries = worktime_tracker.get_week_summaries()
            left_margin = 5
            # TODO: Add colors on ghost plot
            stdscr.addstr(0, left_margin, get_ghost_plot(length=100))
            for i, summary in enumerate(summaries):
                stdscr.addstr(i + 1, left_margin, summary)
            stdscr.refresh()
            time.sleep(REFRESH_RATE)
        except KeyboardInterrupt:
            # TODO: Does not work with curses yet
            options_to_methods = {
                # ["0. Pause for a certain duration": pause,
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


def start():
    curses.wrapper(curses_app)
