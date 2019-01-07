import rumps

from worktime_tracker import WorktimeTracker, seconds_to_human_readable


# TODO: make it update in real time
class WorktimeTrackerStatusBarApp(rumps.App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worktime_tracker = WorktimeTracker()
        self.refresh()

    @rumps.clicked('Refresh')
    def refresh(self):
        self.worktime_tracker.update_state()
        self.menu = [rumps.MenuItem(line) for line in self.worktime_tracker.lines()]
        day_work = self.worktime_tracker.get_work_time_from_weekday(WorktimeTracker.current_weekday())
        self.title = seconds_to_human_readable(day_work)


if __name__ == '__main__':
    WorktimeTrackerStatusBarApp('Worktime Tracker').run()
