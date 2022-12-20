from copy import copy
import time
import datetime

from worktime_tracker.date_utils import get_day_end, get_day_start
from worktime_tracker.logs import Log, reverse_read_logs
from worktime_tracker.constants import STATES_TYPE, WORK_STATES
from worktime_tracker.utils import seconds_to_human_readable


class Interval:
    """Represents an interval of time associated to a given state, i.e. a start and end log."""

    def __init__(self, start_log: Log, end_log: Log):
        assert start_log <= end_log
        assert (
            end_log.timestamp - start_log.timestamp <= 365 * 24 * 60 * 60
        ), f"Intervals cannot be longer than 1 year: {start_log=}, {end_log=}"
        self.start_log = start_log
        self.end_log = end_log
        self.start_datetime = start_log.datetime
        self.end_datetime = end_log.datetime

    @staticmethod
    def convert_logs_to_intervals(logs: list[Log]) -> list["Interval"]:
        return [Interval(start_log, end_log) for start_log, end_log in zip(logs, logs[1:])]

    @staticmethod
    def split_interval_by_day(interval: "Interval") -> list["Interval"]:
        """Split intervals that spans multiple days into multiple intervals or return [interval] if it's not needed

        args: interval
        return: list of intervals
        """
        day_end = get_day_end(interval.start_datetime)
        if interval.end_datetime < day_end:
            return [interval]
        interval_in_day, interval_after_day = interval.split(day_end)
        try:
            return [interval_in_day] + Interval.split_interval_by_day(interval_after_day)
        except RecursionError as e:
            print(interval)
            raise e

    @staticmethod
    def split_intervals_by_day(intervals: list["Interval"]) -> list["Interval"]:
        return [split_interval for interval in intervals for split_interval in Interval.split_interval_by_day(interval)]

    @staticmethod
    def get_intervals_between(
        intervals: list["Interval"], start_datetime: datetime.datetime, end_datetime: datetime.datetime
    ):
        """Get intervals between start_datetime and end_datetime"""
        assert start_datetime <= end_datetime
        intervals_between = []
        for interval in intervals:
            if interval.end_datetime < start_datetime or end_datetime < interval.start_datetime:
                # Discard intervals that doe not overlap with the range
                continue
            if interval.start_datetime < start_datetime:
                _, interval = interval.split(start_datetime)
            if end_datetime < interval.end_datetime:
                interval, _ = interval.split(end_datetime)
            intervals_between.append(interval)
        return intervals_between

    @property
    def state(self) -> STATES_TYPE:
        return self.start_log.state

    @property
    def is_work_interval(self) -> bool:
        return self.state in WORK_STATES

    @property
    def duration(self) -> float:
        return self.end_log.timestamp - self.start_log.timestamp

    @property
    def worktime(self) -> float:
        return self.duration if self.is_work_interval else 0

    def split(self, timestamp: float) -> list["Interval"]:
        split_log = Log(timestamp, self.state)
        assert self.start_log <= split_log <= self.end_log
        return Interval(self.start_log, split_log), Interval(split_log, self.end_log)

    def __eq__(self, other: "Interval") -> bool:
        return self.start_log == other.start_log and self.end_log == other.end_log

    def __repr__(self) -> str:
        start_str = self.start_datetime.strftime("%Y-%m-%d %H:%M:%S")
        return f"Interval<state:{self.state}, start:{start_str}, duration:{seconds_to_human_readable(self.duration)}>"


class Day:
    """Represents a day of logs, i.e. a list of Intervals."""

    def __init__(self, date: datetime.date) -> None:
        self.date = date
        self.intervals = []
        self.day_start = get_day_start(date)
        self.day_end = get_day_end(date)

    @property
    def last_interval(self):
        if len(self.intervals) == 0:
            return None
        return self.intervals[-1]

    def add_interval(self, interval: Interval) -> None:
        assert (
            self.day_start <= interval.start_datetime <= interval.end_datetime <= self.day_end
        ), f"Failed assertion: {self.day_start} <= {interval.start_datetime} <= {interval.end_datetime} <= {self.day_end}"
        # Check that the new interval is not overlapping with the last one
        if self.last_interval is not None and self.last_interval.start_log == interval.start_log:
            # If the last interval is starts at the same moment as the new one, it's probably because it was a dummy one that was added programmatically
            # TODO: It seems that there are many dummy intervals, double check that everything works well
            # print(f"Removing dummy interval {self.last_interval} in favor of {interval}")
            self.intervals.pop()
        if self.last_interval is not None:
            assert (
                self.last_interval.end_datetime <= interval.start_datetime
            ), f"Failed assertion: {self.last_interval} <= {interval}"
        self.intervals.append(interval)

    @property
    def work_intervals(self) -> list[Interval]:
        return [interval for interval in self.intervals if interval.is_work_interval]

    def get_worktime_between(self, start_datetime: datetime.datetime, end_datetime: datetime.datetime) -> float:
        """Get the worktime between start_datetime and end_datetime"""
        return sum(
            interval.worktime
            for interval in Interval.get_intervals_between(self.intervals, start_datetime, end_datetime)
        )

    def get_worktime_at(self, dt_time: datetime.time) -> float:
        assert isinstance(dt_time, datetime.time)

        dt = datetime.datetime.combine(self.day_start, dt_time)
        if dt <= self.day_start:
            dt += datetime.timedelta(days=1)
        assert self.day_start <= dt
        return self.get_worktime_between(self.day_start, dt)

    @property
    def worktime(self) -> float:
        return sum([interval.worktime for interval in self.work_intervals])

    def is_week_day(self) -> bool:
        return self.day_start.weekday() < 5

    def is_work_day(self) -> bool:
        # TODO: Maybe use weekdays as well
        return self.is_week_day() and self.worktime > 4 * 3600

    def __repr__(self) -> str:
        return f"Day(date='{self.date}', worktime='{seconds_to_human_readable(self.worktime)}')"


class ArgsSingleton(type):
    """Creates only one instance per set of arguments"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        key = (cls, args, tuple(kwargs.items()))
        if key not in cls._instances:
            cls._instances[key] = super(ArgsSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[key]


class History(metaclass=ArgsSingleton):
    """Singleton class that tracks the history of worktimes organized by days and intervals."""

    @staticmethod
    def clear() -> None:
        """Clear the history singleton"""
        History._instances.clear()

    def __init__(self, dont_read_before=datetime.datetime.now() - datetime.timedelta(days=365), refresh_rate=1) -> None:
        print("Initializing history...")
        self._days_dict = {}
        # TODO: We should raise an error when trying to get worktime before the dont_read_before date
        self.dont_read_before = dont_read_before if dont_read_before is not None else datetime.datetime.min
        self._last_read_log = None
        self._last_refresh = None
        self.refresh_rate = refresh_rate
        self.refresh()
        print("History initialized")

    @property
    def days(self):
        return list(self._days_dict.values())

    @property
    def all_intervals(self):
        # TODO: Deprecate to use day abstraction instead?
        return [interval for day in self.days for interval in day.intervals]

    @property
    def current_day(self):
        return self.days[-1]

    def refresh(self) -> None:
        if self._last_refresh is not None and time.time() - self._last_refresh < self.refresh_rate:
            return
        self.add_intervals(self.get_new_intervals())
        self._last_refresh = time.time()

    def add_intervals(self, intervals: list[Interval]) -> None:
        for interval in Interval.split_intervals_by_day(intervals):
            start_date = get_day_start(interval.start_datetime).date()
            if start_date not in self._days_dict:
                self._days_dict[start_date] = Day(date=start_date)
            self._days_dict[start_date].add_interval(interval)

    def get_new_logs(self) -> list[Log]:
        new_logs = []
        # Read file in reverse to find new logs that are not loaded yet
        for log in reverse_read_logs():
            if log.datetime <= self.dont_read_before:
                break
            if self._last_read_log is not None and log <= self._last_read_log:
                break
            new_logs.append(log)
        new_logs = new_logs[::-1]
        if len(new_logs) > 0:
            self._last_read_log = copy(new_logs[-1])
        return new_logs

    def get_new_intervals(self) -> list[Interval]:
        last_log = copy(self._last_read_log)  # We need to retrieve it before calling get_new_logs()
        new_logs = self.get_new_logs()
        # Add dummy log so that we take the last interval into account
        logs = [*new_logs, Log(time.time(), "dummy")]
        if last_log is not None:
            # FIXME: Sometimes the last log is more recent that logs[0]
            # I.e. I hust had the result being: [Log<date=2021-08-25 18:01:05, state=dummy>, Log<date=2022-08-25 17:59:58, state=personal>, Log<date=2022-08-25 18:02:04, state=dummy>]
            logs = [last_log, *logs]  # Prepend last log to logs to count the initial interval
        return Interval.convert_logs_to_intervals(logs)

    def get_worktime_between(
        self,
        start_datetime: datetime.datetime,
        end_datetime: datetime.datetime,
        dont_count_days: list[datetime.date] = None,
    ) -> float:
        assert start_datetime <= end_datetime, f"Failed assertion: {start_datetime} <= {end_datetime}"
        self.refresh()
        if dont_count_days is None:
            dont_count_days = []
        # Assign the date to a variable as it might be can be called millions of times
        start_date = get_day_start(start_datetime).date()
        end_date = get_day_end(end_datetime).date()
        days = [day for day in self.days if start_date <= day.date <= end_date and day.date not in dont_count_days]
        return sum(day.get_worktime_between(start_datetime, end_datetime) for day in days)

    def __getitem__(self, i) -> Day:
        """Get a specific day."""
        return list(self._days_dict.values())[i]

    def __repr__(self) -> str:
        return f"{list(self._days_dict.values())}"
