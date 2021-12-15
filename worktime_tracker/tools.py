from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
import subprocess

import numpy as np
import pandas as pd
import plotly.express as px

from worktime_tracker.constants import WORK_STATES
from worktime_tracker.date_utils import (
    get_current_day_end,
    get_current_day_start,
    get_current_weekday,
    coerce_to_datetime,
)
from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.worktime_tracker import get_work_time, get_days
from worktime_tracker.logs import rewrite_history, read_first_log, get_all_logs, convert_logs_to_intervals
from worktime_tracker.worktime_tracker import WorktimeTracker, get_average_work_time_at


def rewrite_history_prompt():
    now = datetime.now()
    start = input("Start time? (hh:mm): ")
    start_hour, start_minute = [int(x) for x in start.split(":")]
    end = input("End time? (hh:mm): ")
    end_hour, end_minute = [int(x) for x in end.split(":")]
    day_offset = input("Day offset? (default=0): ")
    day_offset = int(day_offset) if day_offset != "" else 0
    start = (
        (now + timedelta(days=day_offset))
        .replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
        .timestamp()
    )
    end = (
        (now + timedelta(days=day_offset))
        .replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
        .timestamp()
    )
    new_state = input("New state?: ")
    rewrite_history(start, end, new_state)


def get_productivity_plot(start_datetime: datetime, end_datetime: datetime):
    def format_timestamp(timestamp):
        d = datetime.fromtimestamp(timestamp)
        return f"{d.hour}h{d.minute:02d}"

    start_timestamp = start_datetime.timestamp()
    end_timestamp = end_datetime.timestamp()
    bin_size = 15 * 60
    n_bins = int((end_timestamp - start_timestamp) / bin_size)
    end_timestamp = start_timestamp + n_bins * bin_size
    bin_starts = np.arange(start_timestamp, end_timestamp, bin_size)
    bin_ends = bin_starts + bin_size
    table = []
    for bin_start, bin_end in zip(bin_starts, bin_ends):
        table.append(
            {
                # Very slow for old logs, would be better to use Discretizer
                "work_time": get_work_time(coerce_to_datetime(bin_start), coerce_to_datetime(bin_end)),
                "bin_start": bin_start,
                "bin_end": bin_end,
                "formatted_start_time": format_timestamp(bin_start),
            }
        )
    total_work_time = get_work_time(start_datetime, end_datetime)
    df = pd.DataFrame(table).sort_values("bin_start")
    df["work_time_m"] = df["work_time"] / 60
    fig = px.histogram(
        df,
        x="formatted_start_time",
        y="work_time_m",
        histfunc="sum",
        title=f"Total Work Time = {seconds_to_human_readable(total_work_time)}",
    )
    return fig


def get_todays_productivity_plot():
    start_datetime = get_current_day_start()
    end_datetime = min(get_current_day_end(), datetime.now())
    return get_productivity_plot(start_datetime, end_datetime)


def download_productivity_plot(path="productivity_plot.png"):
    get_todays_productivity_plot().write_image(path)
    return path


def plot_productivity():
    productivity_plot_path = download_productivity_plot()
    # TODO: Only works on macos for now
    subprocess.run(["open", productivity_plot_path], check=True)


class Discretizer:
    def __init__(self, step, add_empty_bins=True):
        first_log = read_first_log()
        first_datetime = first_log.datetime.replace(minute=0, second=0, microsecond=0)
        last_datetime = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.first_timestamp = first_datetime.timestamp()
        self.last_timestamp = last_datetime.timestamp()
        self.step = step
        if add_empty_bins:
            self.worktime_accumulator = {bin_start: 0 for bin_start in self.get_bin_starts()}
        else:
            self.worktime_accumulator = defaultdict(float)

    def get_bin_starts(self):
        n_bins = int((self.last_timestamp - self.first_timestamp) // self.step)
        return [self.first_timestamp + i * self.step for i in range(n_bins)]

    def add_interval(self, interval):
        if interval.state not in WORK_STATES:
            return
        assert self.first_timestamp <= interval.start_timestamp and interval.end_timestamp <= self.last_timestamp
        n_steps_since_start = (interval.start_timestamp - self.first_timestamp) // self.step
        bin_start = self.first_timestamp + n_steps_since_start * self.step
        bin_end = bin_start + self.step
        if interval.end_timestamp > bin_end:
            # print("Split ", interval, bin_start, bin_end)
            for split_interval in interval.split(bin_end):
                self.add_interval(split_interval)
        else:
            # print("Accumulating", interval, interval.end_timestamp - bin_start)
            self.worktime_accumulator[bin_start] += interval.duration

    def to_df(self):
        records = []
        for timestamp, work_time in self.worktime_accumulator.items():
            dt = datetime.fromtimestamp(timestamp)
            records.append(
                {
                    "work_time": work_time,
                    "start_datetime": dt,
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "year_month": dt.strftime("Y:%y %b"),
                    "year_week": dt.strftime("Y:%y w:%V"),
                    "year_day": dt.strftime("Y:%y %b d:%d"),
                    "formatted_date": dt.strftime("%Y-%m-%d"),
                    "dow": dt.strftime("%A"),
                }
            )
        return pd.DataFrame(records)


@lru_cache()
def get_hourly_worktime_df():
    logs = get_all_logs()
    intervals = convert_logs_to_intervals(logs)
    discretizer = Discretizer(step=3600)
    for interval in intervals:
        discretizer.add_interval(interval)
    df_hourly = discretizer.to_df()
    df_hourly["work_time"] /= 3600
    return df_hourly


def get_daily_worktime_df():
    df_hourly = get_hourly_worktime_df()
    daily_columns = [col for col in df_hourly.columns if col not in ["hour", "start_datetime", "work_time"]]
    return (
        df_hourly.groupby(daily_columns)["start_datetime", "work_time"]
        .agg({"start_datetime": "min", "work_time": "sum"})
        .reset_index()
    )


def create_ghost_plot(your_position, ghost_position, length=100):
    def add_icon_on_plot(plot, icon, position):
        assert 0 <= position <= 1
        position_idx = int(position * len(plot))
        plot_as_list = list(plot)  # Use list because strings don't support item assignment
        for i, char in enumerate(icon):
            if position_idx + i >= len(plot_as_list):
                break
            plot_as_list[position_idx + i] = char
        return "".join(plot_as_list)

    plot = "-" * length
    plot = add_icon_on_plot(plot=plot, icon="[Ghost]", position=ghost_position)
    plot = add_icon_on_plot(plot=plot, icon="[You]", position=your_position)
    return f"[{plot}]"


def get_ghost_plot(length=100):
    days = get_days()
    target = WorktimeTracker.targets[get_current_weekday()]
    if target == 0:
        return ""
    ghost_work_time = get_average_work_time_at(days, datetime.now().time())
    ghost_position = min(ghost_work_time / target, 1)
    your_worktime = WorktimeTracker.get_work_time_from_weekday(get_current_weekday())
    your_position = min(your_worktime / target, 1)
    return create_ghost_plot(your_position=your_position, ghost_position=ghost_position, length=length)
