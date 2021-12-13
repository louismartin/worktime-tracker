from worktime_tracker.tools import get_todays_productivity_plot, get_ghost_plot


def test_get_todays_productivity_plot():
    """Check that get_todays_productivity_plot does not raise an error."""
    assert get_todays_productivity_plot() is not None


def test_get_ghost_plot():
    assert get_ghost_plot(length=50) is not None
