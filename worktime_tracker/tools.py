from collections import defaultdict
from datetime import datetime, timedelta
from functools import lru_cache
import subprocess
import time
import tempfile

import numpy as np
import pandas as pd
import plotly.express as px
from tqdm import tqdm

from worktime_tracker.constants import WORK_STATES
from worktime_tracker.date_utils import (
    get_current_day_end,
    get_current_day_start,
    get_current_weekday,
    coerce_to_datetime,
    parse_time,
)
from worktime_tracker.history import History
from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.worktime_tracker import get_worktime_between, get_worktime_from_weekday
from worktime_tracker.logs import rewrite_history
from worktime_tracker.worktime_tracker import WorktimeTracker


def rewrite_history_prompt():
    now = datetime.now()
    start = input("Start time? (hh:mm): ")
    start_hour, start_minute = [int(x) for x in start.split(":")]
    end = input("End time? (hh:mm): ")
    end_hour, end_minute = [int(x) for x in end.split(":")]
    day_offset = input("Day offset? (default=0): ")
    day_offset = int(day_offset) if day_offset != "" else 0
    start_datetime = (now + timedelta(days=day_offset)).replace(
        hour=start_hour, minute=start_minute, second=0, microsecond=0
    )
    end_datetime = (now + timedelta(days=day_offset)).replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    new_state = input("New state?: ")
    rewrite_history(start_datetime, end_datetime, new_state)


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
                "worktime": get_worktime_between(coerce_to_datetime(bin_start), coerce_to_datetime(bin_end)),
                "bin_start": bin_start,
                "bin_end": bin_end,
                "formatted_start_time": format_timestamp(bin_start),
            }
        )
    total_worktime = get_worktime_between(start_datetime, end_datetime)
    df = pd.DataFrame(table).sort_values("bin_start")
    df["worktime_m"] = df["worktime"] / 60
    fig = px.histogram(
        df,
        x="formatted_start_time",
        y="worktime_m",
        histfunc="sum",
        title=f"Total Work Time = {seconds_to_human_readable(total_worktime)}",
    )
    return fig


def get_todays_productivity_plot():
    start_datetime = get_current_day_start()
    end_datetime = min(get_current_day_end(), datetime.now())
    return get_productivity_plot(start_datetime, end_datetime)


def download_productivity_plot(path=None):
    if path is None:
        # Temporary path
        path = tempfile.mktemp(suffix=".png")
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
        assert (
            self.first_timestamp <= interval.start_log.start_timestamp and interval.end_timestamp <= self.last_timestamp
        )
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
        for timestamp, worktime in self.worktime_accumulator.items():
            dt = datetime.fromtimestamp(timestamp)
            records.append(
                {
                    "worktime": worktime,
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
    intervals = History().all_intervals
    discretizer = Discretizer(step=3600)
    for interval in intervals:
        discretizer.add_interval(interval)
    df_hourly = discretizer.to_df()
    df_hourly["worktime"] /= 3600
    return df_hourly


def get_daily_worktime_df():
    df_hourly = get_hourly_worktime_df()
    daily_columns = [col for col in df_hourly.columns if col not in ["hour", "start_datetime", "worktime"]]
    return (
        df_hourly.groupby(daily_columns)["start_datetime", "worktime"]
        .agg({"start_datetime": "min", "worktime": "sum"})
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


def get_worktimes_at(days, dt_time):
    return [day.get_worktime_at(dt_time) for day in days if day.is_work_day()]


def get_average_worktime_at(days, dt_time):
    worktimes_at = get_worktimes_at(days, dt_time)
    return sum(worktimes_at) / len(worktimes_at)


def get_quantile_worktime_at(days, dt_time, quantile):
    worktimes_at = get_worktimes_at(days, dt_time)
    return np.quantile(worktimes_at, quantile)


def get_ghost_plot(length=100):
    # TODO: Take timezone into account
    days = History().days
    target = WorktimeTracker.targets[get_current_weekday()]
    if target == 0:
        return ""
    # Higher quantile = ghost calibrated on your best days, lower quantile = ghost calibrated on your worst days
    ghost_worktime = get_quantile_worktime_at(days, datetime.now().time(), quantile=0.75)
    ghost_position = min(ghost_worktime / target, 1)
    your_worktime = get_worktime_from_weekday(get_current_weekday())
    your_position = min(your_worktime / target, 1)
    return create_ghost_plot(your_position=your_position, ghost_position=ghost_position, length=length)


def pause():
    duration = parse_time(input("Enter a duration to pause during a certain time (e.g. 2h30).\nDuration: "))
    if duration is not None:
        print(f"Pausing for {duration}.")
        for _ in tqdm(range(duration.seconds)):
            time.sleep(1)
