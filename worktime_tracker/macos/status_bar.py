import rumps

from worktime_tracker.worktime_tracker import WorktimeTracker


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
            self.title = lines[0].split(': ')[1]
        except Exception as e:
            self.title = 'ERROR'
            raise e


def start():
    StatusBarApp().run()
