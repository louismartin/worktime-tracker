from datetime import datetime, timedelta
import os
from pathlib import Path
import sys


REPO_DIR = Path(__file__).resolve().parent.parent
LOGS_PATH = REPO_DIR / 'logs.tsv'
LAST_CHECK_PATH = REPO_DIR / 'last_check'


def get_state():
    if sys.platform == 'darwin':
        from worktime_tracker.macos.get_state import get_state
        return get_state()
    if sys.platform == 'win32':
        from worktime_tracker.windows.get_state import get_state
        return get_state()

    raise NotImplementedError('OS {sys.platform} is not supported yet')


def reverse_read_line(filename, buf_size=8192):
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


def seconds_to_human_readable(seconds):
    sign = (lambda x: ('', '-')[x < 0])(seconds)
    seconds = int(abs(seconds))
    sec = timedelta(seconds=seconds)
    d = datetime(1, 1, 1) + sec
    return f'{sign}{d.hour}h{d.minute:02d}m'
