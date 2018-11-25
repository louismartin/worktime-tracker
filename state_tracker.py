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

    states = ['work', 'leisure', 'locked']

    def __init__(self):
        self.cum_times = {state: 0 for state in self.states}
        self.logs_path = repo_dir / 'logs.tsv'
        self.logs_path.touch()  # Creates file if it does not exist
        self.last_check_path = repo_dir / 'last_check'
        self.logs = []
        self.load_logs()

    def update_cum_times(self, logs):
        for (start_timestamp, state), (end_timestamp, next_state) in zip(logs[:-1], logs[1:]):
            assert state != next_state
            self.cum_times[state] += (end_timestamp - start_timestamp)

    def write_log(self, timestamp, state):
        with self.logs_path.open('a') as f:
            f.write(f'{timestamp}\t{state}\n')

    def append_and_write_log(self, timestamp, state):
        self.logs.append((timestamp, state))
        self.write_log(timestamp, state)

    def write_last_check(self, timestamp):
        with self.last_check_path.open('w') as f:
            f.write(str(timestamp) + '\n')

    def read_last_check(self):
        with self.last_check_path.open('r') as f:
            return float(f.readline().strip())

    def read_last_log(self):
        try:
            last_line = next(reverse_readline(self.logs_path))
        except StopIteration:
            return None
        timestamp, state = last_line.strip().split('\t')
        return float(timestamp), state

    def was_run_today(self):
        last_log = self.read_last_log()
        if last_log is None:
            return False
        timestamp, _ = last_log
        return is_today(timestamp)

    def get_todays_logs(self):
        logs = []
        for line in reverse_readline(self.logs_path):
            timestamp, state = line.strip().split('\t')
            if not is_today(float(timestamp)):
                break
            logs.append((float(timestamp), state))
        return logs[::-1]  # We read the logs backward

    def load_logs(self):
        # TODO: If the program was killed two hours ago on work state, then it will probably count two hours of work
        if not self.was_run_today():
            self.write_log(time.time(), 'locked')
        if self.read_last_log()[1] != 'locked':
            # Add a log pretending the computer was locked at the last time the state was checked
            self.write_log(self.read_last_check(), 'locked')
        self.logs = self.get_todays_logs()
        self.update_cum_times(self.logs)

    def update_state(self):
        state = get_state()
        timestamp = time.time()
        self.write_last_check(timestamp)
        last_timestamp, last_state = self.logs[-1]
        if state == last_state:
            return
        self.append_and_write_log(timestamp, state)
        # Update cumulative times
        self.update_cum_times([(last_timestamp, last_state), (timestamp, state)])


if __name__ == '__main__':
    state_tracker = StateTracker()
    while True:
        state_tracker.update_state()
        time.sleep(0.1)
