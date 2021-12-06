from datetime import datetime, timedelta
from functools import lru_cache
import time
import math

import numpy as np
import pandas as pd
import plotly.express as px
from tqdm import tqdm

from worktime_tracker.utils import seconds_to_human_readable
from worktime_tracker.worktime_tracker import rewrite_history, get_work_time, WorktimeTracker, read_first_log


def rewrite_history(start_timestamp, end_timestamp, new_state):
    # Careful, this methods rewrites the entire log file
    shutil.copy(LOGS_PATH, f'{LOGS_PATH}.bck{int(time.time())}')
    with LOGS_PATH.open('r') as f:
        logs = get_logs(start_timestamp=0, end_timestamp=time.time())
    new_logs = get_rewritten_history_logs(start_timestamp, end_timestamp, new_state, logs)
    with LOGS_PATH.open('w') as f:
        for timestamp, state in new_logs:
            f.write(f'{timestamp}\t{state}\n')
    global ALL_LOGS
    ALL_LOGS[:] = []  # Reset logs


def rewrite_history_prompt():
    now = datetime.now()
    start = input('Start time? (hh:mm): ')
    start_hour, start_minute = [int(x) for x in start.split(':')]
    end = input('End time? (hh:mm): ')
    end_hour, end_minute = [int(x) for x in end.split(':')]
    day_offset = input('Day offset? (default=0): ')
    day_offset = int(day_offset) if day_offset != '' else 0
    start = (now + timedelta(days=day_offset)).replace(hour=start_hour, minute=start_minute, second=0, microsecond=0).timestamp()
    end = (now + timedelta(days=day_offset)).replace(hour=end_hour, minute=end_minute, second=0, microsecond=0).timestamp()
    new_state = input('New state?: ')
    rewrite_history(start, end, new_state)


def get_productivity_plot(start_timestamp, end_timestamp):
    def format_timestamp(timestamp):
        d = datetime.fromtimestamp(timestamp)
        return f'{d.hour}h{d.minute:02d}'

    bin_size = 15 * 60
    n_bins = int((end_timestamp - start_timestamp) / bin_size)
    end_timestamp = start_timestamp + n_bins * bin_size
    bin_starts = np.arange(start_timestamp, end_timestamp, bin_size)
    bin_ends = bin_starts + bin_size
    table = []
    for bin_start, bin_end in zip(bin_starts, bin_ends):
        table.append(
            {'work_time': get_work_time(bin_start, bin_end), 'bin_start': bin_start, 'bin_end': bin_end, 'formatted_start_time': format_timestamp(bin_start)}
        )
    total_work_time = get_work_time(start_timestamp, end_timestamp)
    df = pd.DataFrame(table).sort_values('bin_start')
    df['work_time_m'] = df['work_time'] / 60
    fig = px.histogram(df, x='formatted_start_time', y='work_time_m', histfunc='sum', title=f'Total Work Time = {seconds_to_human_readable(total_work_time)}')
    return fig


def get_todays_productivity_plot():
    interval = 1 * 24 * 60 * 60
    start_timestamp = WorktimeTracker.get_current_day_start()
    end_timestamp = min(start_timestamp + interval, time.time())
    return get_productivity_plot(start_timestamp, end_timestamp)


def download_productivity_plot(path='productivity_plot.png'):
    get_todays_productivity_plot().write_image(path)
    return path


@lru_cache()
def get_hourly_worktime_df():
    first_timestamp, _ = read_first_log()
    first_datetime = datetime.fromtimestamp(first_timestamp).replace(minute=0, second=0, microsecond=0)
    end_datetime = datetime.now().replace(minute=0, second=0, microsecond=0)
    table = []
    total = math.ceil((end_datetime - first_datetime).total_seconds() / 3600)
    with tqdm(total=total) as pbar:
        while end_datetime >= first_datetime:
            start_datetime = end_datetime - timedelta(hours=1)
            start_timestamp = start_datetime.timestamp()
            # Weird behaviour with daylight savings time, start and end are equal
            end_timestamp = max(end_datetime.timestamp(), start_timestamp + 1)
            table.append({
                'work_time': get_work_time(start_timestamp, end_timestamp) / 3600,
                'start_datetime': start_datetime,
                'year': start_datetime.year,
                'month': start_datetime.month,
                'day': start_datetime.day,
                'hour': start_datetime.hour,
                'year_month': start_datetime.strftime('Y:%y %b'),
                'year_week': start_datetime.strftime('Y:%y w:%V'),
                'year_day': start_datetime.strftime('Y:%y %b d:%d'),
                'formatted_date': start_datetime.strftime('%Y-%m-%d'),
                'dow': start_datetime.strftime('%A'),
            })
            end_datetime = start_datetime
            pbar.update(1)
    return pd.DataFrame(table).sort_values('start_datetime')


def get_daily_worktime_df():
    df_hourly = get_hourly_worktime_df()
    daily_columns = [col for col in df_hourly.columns if col not in ['hour', 'start_datetime', 'work_time']]
    return df_hourly.groupby(daily_columns)['start_datetime', 'work_time'].agg({'start_datetime': 'min', 'work_time': 'sum'}).reset_index()
