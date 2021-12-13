from worktime_tracker.worktime_tracker import WorktimeTracker


# TODO: Check how to use fixtures
def test_worktime_tracker():
    worktime_tracker = WorktimeTracker()
    worktime_tracker.check_state()
    print("\n".join(worktime_tracker.get_week_summaries()))
