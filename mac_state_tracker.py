from collections import defaultdict
from datetime import datetime
import os
from pathlib import Path
import subprocess
import time

import Quartz


repo_dir = Path(__file__).resolve().parent


def get_desktop_number():
    script_path = repo_dir / 'get_desktop_wallpaper.scpt'
    process = subprocess.run(['osascript', str(script_path)], capture_output=True, check=True)
    wallpaper = process.stdout.decode('utf-8').strip()
    return {
        'Facebook_Backgrounds--node_facebook (1).png': 1,
        'Facebook_Backgrounds--friendsgc.png': 2,
        'Yosemite 5.jpg': 3,
    }[wallpaper]


def is_screen_locked():
    return Quartz.CGSessionCopyCurrentDictionary().get('CGSSessionScreenIsLocked', 0) == 1


def get_state():
    desktop_number = get_desktop_number()
    if is_screen_locked():
        return 'locked'
    if desktop_number in [1, 2]:
        return 'work'
    if desktop_number in [3]:
        return 'leisure'
    raise


def reverse_readline(filename, buf_size=8192):
    '''a generator that returns the lines of a file in reverse order'''
    with open(filename) as fh:
        segment = None
        offset = 0
        fh.seek(0, os.SEEK_END)
        file_size = remaining_size = fh.tell()
        while remaining_size > 0:
            offset = min(file_size, offset + buf_size)
            fh.seek(file_size - offset)
            buffer = fh.read(min(remaining_size, buf_size))
            remaining_size -= buf_size
            lines = buffer.split('\n')
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != '\n':
                    lines[-1] += segment
                else:
                    yield segment
            segment = lines[0]
            for index in range(len(lines) - 1, 0, -1):
                if lines[index]:
                    yield lines[index]
        # Don't yield None if the file was empty
        if segment is not None:
            yield segment


def is_today(timestamp):
    query_datetime = datetime.fromtimestamp(timestamp)
    current_datetime = datetime.fromtimestamp(time.time())
    # Current day starts at 7
    return query_datetime.date() == current_datetime.date() and query_datetime.hour >= 7


class StateTracker:

    def __init__(self):
        self.logs_path = repo_dir / 'logs.tsv'
        self.logs = []
        self.load_logs()
        self.cum_times = defaultdict(float)

    def update_cum_times(self, logs):
        for (start_timestamp, state), (end_timestamp, next_state) in zip(logs[:-1], logs[1:]):
            assert state != next_state
            self.cum_times[state] += (end_timestamp - start_timestamp)

    def load_logs(self):
        self.logs_path.touch()  # Creates file if it does not exist
        for line in reverse_readline(self.logs_path):
            timestamp, state = line.strip().split('\t')
            if not is_today(float(timestamp)):
                break
            self.logs.append((float(timestamp), state))
        if len(self.logs) == 0:
            # If file was just created or no logs for today yet, we create one
            timestamp = time.time()
            state = get_state()
            self.logs.append((timestamp, state))
            with self.logs_path.open('a') as f:
                f.write(f'{timestamp}\t{state}\n')
        self.update_cum_times(self.logs)

    def update_state(self):
        state = get_state()
        timestamp = time.time()
        last_timestamp, last_state = self.logs[-1]
        if state == last_state:
            return
        # Write and save state
        self.logs.append((timestamp, state))
        with self.logs_path.open('a') as f:
            f.write(f'{timestamp}\t{state}\n')
        # Update cumulative times
        self.update_cum_times([(last_timestamp, last_state), (timestamp, state)])
        print(self.cum_times)


if __name__ == '__main__':
    state_tracker = StateTracker()
    while True:
        state_tracker.update_state()
        time.sleep(0.1)
