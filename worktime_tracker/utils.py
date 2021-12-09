from datetime import datetime, timedelta
import os
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
LOGS_PATH = REPO_DIR / '.logs/logs.tsv'
LAST_CHECK_PATH = REPO_DIR / 'last_check.txt'
SPACE_TYPES_PATH = REPO_DIR / 'space_types.json'
LOGS_PATH.parent.mkdir(exist_ok=True)


def reverse_read_lines(filename, buf_size=8192):
    '''a generator that returns the lines of a file in reverse order'''
    with open(filename, encoding="utf8") as fh:
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
    sign = '' if seconds >= 0 else '-'
    seconds = int(abs(seconds))  # Convert to positive
    td = timedelta(seconds=seconds)
    days = td.days
    hours = td.seconds//3600
    minutes = (td.seconds//60)%60
    days = f'{days}d ' if days > 0 else ''
    hours = f'{hours}h ' if hours > 0 else ''
    minutes = f'{minutes:02d}m'
    if days == '':
        hours = hours.strip(' ')  # Display as 3d 2h 25 but as 2h25 if no days
    return f'{sign}{days}{hours}{minutes}'.strip()


def yield_lines(filepath):
    with open(filepath, 'r', encoding='utf8') as f:
        for line in f:
            yield line.strip('\n')
