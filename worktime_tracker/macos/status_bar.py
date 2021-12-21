import time
from functools import wraps

import rumps

from worktime_tracker.constants import REFRESH_RATE
from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.tools import get_ghost_plot, rewrite_history_prompt, plot_productivity, pause


NO_ALERT_UNTIL = time.time()


def discard_args(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func()

    return wrapper


class StatusBarApp(rumps.App):
    def __init__(self, *args, **kwargs):
        super().__init__(name="", *args, **kwargs)
        self.worktime_tracker = WorktimeTracker()
        self.no_alert_until = time.time()
        self.refresh(None)

    def maybe_send_alert(self):
        is_work_state = self.worktime_tracker.is_work_state(self.worktime_tracker.current_state)
        work_ratio_last_period = self.worktime_tracker.get_work_ratio_since_timestamp(time.time() - 3600 / 2)
        if time.time() < self.no_alert_until:
            return
        if 0.1 < work_ratio_last_period < 0.80 and not is_work_state:
            rumps.notification("Go back to work!", "", f"Your work ratio is {int(work_ratio_last_period*100)}%")
            self.no_alert_until = time.time() + 5 * 60
        if work_ratio_last_period > 0.95 and is_work_state:
            rumps.notification("Good job!", "", "")
            self.no_alert_until = time.time() + 10 * 60

    @rumps.timer(REFRESH_RATE)
    def refresh(self, _):
        try:
            self.worktime_tracker.check_state()
            self.title = self.worktime_tracker.get_instant_summary()
            # Get lines to display
            lines = self.worktime_tracker.get_week_summaries()
            # Update menu with new times
            self.menu.clear()
            self.menu = lines[1:][::-1]  # Sort days in chronological order
            self.menu.add(get_ghost_plot(length=30))
            buttons_with_callbacks = {
                "Plot productivity": discard_args(plot_productivity),  # The callbacks take a sender arg that we don't use
                # TODO: Find a way to get an input field for pause and rewrite history
                "Pause (CLI)": discard_args(pause),
                "Rewrite history (CLI)": discard_args(rewrite_history_prompt),
                "Quit": rumps.quit_application,
            }
            for button_name, callback in buttons_with_callbacks.items():
                button = rumps.MenuItem(button_name)
                button.set_callback(callback)
                self.menu.add(button)
            self.maybe_send_alert()
        except Exception as e:
            self.title = "ERROR"
            print(e)
            raise e


def start():
    StatusBarApp().run()
