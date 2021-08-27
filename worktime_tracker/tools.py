from datetime import datetime, timedelta
import time

import numpy as np
import pandas as pd
import plotly.express as px

from worktime_tracker.worktime_tracker import rewrite_history, get_work_time, WorktimeTracker


def rewrite_history_prompt():
    now = datetime.now()
    start = input('Start time? (hh:mm): ')
    start_hour, start_minute = [int(x) for x in start.split(':')]
    end = input('End time? (hh:mm): ')
    end_hour, end_minute = [int(x) for x in end.split(':')]
    day_offset = 0  # day_offset = input('Day offset? (default=0)')
    day_offset = int(day_offset) if day_offset != '' else 0
    start = (now + timedelta(days=day_offset)).replace(hour=start_hour, minute=start_minute, second=0, microsecond=0).timestamp()
    end = (now + timedelta(days=day_offset)).replace(hour=end_hour, minute=end_minute, second=0, microsecond=0).timestamp()
    new_state = input('New state?: ')
    rewrite_history(start, end, new_state)


def get_productivity_plot(start_timestamp, end_timestamp):
    def format_timestamp(timestamp):
        d = datetime.fromtimestamp(timestamp)
        return f'{d.hour}h{d.minute:02d}'

    bin_size = 10 * 60
    n_bins = int((end_timestamp - start_timestamp) / bin_size)
    end_timestamp = start_timestamp + n_bins * bin_size
    bin_starts = np.arange(start_timestamp, end_timestamp, bin_size)
    bin_ends = bin_starts + bin_size
    table = []
    for bin_start, bin_end in zip(bin_starts, bin_ends):
        table.append(
            {'work_time': get_work_time(bin_start, bin_end), 'bin_start': bin_start, 'bin_end': bin_end, 'formatted_start_time': format_timestamp(bin_start)}
        )
    df = pd.DataFrame(table).sort_values('bin_start')
    df['work_time_m'] = df['work_time'] / 60
    fig = px.histogram(df, x='formatted_start_time', y='work_time_m', histfunc='sum')
    return fig


def get_todays_productivity_plot():
    interval = 1 * 24 * 60 * 60
    start_timestamp = WorktimeTracker.get_current_day_start()
    end_timestamp = min(start_timestamp + interval, time.time())
    return get_productivity_plot(start_timestamp, end_timestamp)


def download_productivity_plot(path='productivity_plot.png'):
    get_todays_productivity_plot().write_image(path)
    return path
