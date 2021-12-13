import time

import rumps

from worktime_tracker.constants import REFRESH_RATE
from worktime_tracker.worktime_tracker import WorktimeTracker


NO_ALERT_UNTIL = time.time()


class StatusBarApp(rumps.App):
    def __init__(self, *args, **kwargs):
        super().__init__(name="", *args, **kwargs)
        self.worktime_tracker = WorktimeTracker()
        self.refresh(None)
        self.no_alert_until = time.time()

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
            # Get lines to display
            lines = self.worktime_tracker.get_week_summaries()
            # Update menu with new times
            self.menu.clear()
            self.menu = lines[1:][::-1]  # Sort days in chronological order
            # Add quit button again
            quit_button = rumps.MenuItem("Quit")
            quit_button.set_callback(rumps.quit_application)
            self.menu.add(quit_button)
            self.title = self.worktime_tracker.get_instant_summary()
            self.maybe_send_alert()
        except Exception as e:
            self.title = "ERROR"
            print(e)
            raise e


def start():
    StatusBarApp().run()
