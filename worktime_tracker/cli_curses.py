import time
import curses

from worktime_tracker.constants import REFRESH_RATE
from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.tools import get_ghost_plot


def curses_app(stdscr):
    # Clear screen
    stdscr.clear()
    worktime_tracker = WorktimeTracker()
    while True:
        worktime_tracker.check_state()
        summaries = worktime_tracker.get_week_summaries()
        left_margin = 5
        # TODO: Add colors on ghost plot
        stdscr.addstr(0, left_margin, get_ghost_plot(length=100))
        for i, summary in enumerate(summaries):
            stdscr.addstr(i + 1, left_margin, summary)
        stdscr.refresh()
        time.sleep(REFRESH_RATE)
        # TODO: Add tools like rewrite history (see cli.py)


def start():
    curses.wrapper(curses_app)
