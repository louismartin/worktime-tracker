import time

import rumps

from worktime_tracker.worktime_tracker import WorktimeTracker
from worktime_tracker.utils import seconds_to_human_readable


class StatusBarApp(rumps.App):

    def __init__(self, *args, **kwargs):
        super().__init__(name='', *args, **kwargs)
        self.worktime_tracker = WorktimeTracker()
        self.refresh(None)

    @rumps.timer(1)
    def refresh(self, _):
        try:
            self.worktime_tracker.check_state()
            # Get lines to display
            lines = self.worktime_tracker.lines()
            # Update menu with new times
            self.menu.clear()
            self.menu = lines[1:][::-1]  # Sort days in chronological order
            # Add quit button again
            quit_button = rumps.MenuItem('Quit')
            quit_button.set_callback(rumps.quit_application)
            self.menu.add(quit_button)
            work_ratio_last_period = self.worktime_tracker.get_work_ratio_since_timestamp(time.time() - 3600/2)
            work_time_today = self.worktime_tracker.get_work_time_from_weekday(self.worktime_tracker.current_weekday())
            self.title = f'{int(100 * work_ratio_last_period)}% - {seconds_to_human_readable(work_time_today)}'
        except Exception as e:
            self.title = 'ERROR'
            raise e


def start():
    StatusBarApp().run()
