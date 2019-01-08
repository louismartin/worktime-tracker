import rumps

from worktime_tracker import WorktimeTracker, seconds_to_human_readable


# TODO: make it update in real time
class WorktimeTrackerStatusBarApp(rumps.App):

    def __init__(self, *args, **kwargs):
        super().__init__(name='', *args, **kwargs)
        self.worktime_tracker = WorktimeTracker()
        self.refresh(None)

    @rumps.timer(1)
    def refresh(self, _):
        # TODO: update work time in real time instead of only when changing state
        self.worktime_tracker.check_state()
        for i, line in enumerate(self.worktime_tracker.lines()):
            self.menu[i] = rumps.MenuItem(line)
        day_work = self.worktime_tracker.get_work_time_from_weekday(WorktimeTracker.current_weekday())
        self.title = seconds_to_human_readable(day_work)


if __name__ == '__main__':
    WorktimeTrackerStatusBarApp().run()
