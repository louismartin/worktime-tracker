from datetime import timedelta
import os


def reverse_read_lines(filename, buf_size=8192):
    """a generator that returns the lines of a file in reverse order"""
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
            lines = buffer.split("\n")
            # the first line of the buffer is probably not a complete line so
            # we'll save it and append it to the last line of the next buffer
            # we read
            if segment is not None:
                # if the previous chunk starts right from the beginning of line
                # do not concact the segment to the last line of new chunk
                # instead, yield the segment first
                if buffer[-1] != "\n":
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
    sign = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))  # Convert to positive
    td = timedelta(seconds=seconds)

    days = td.days
    hours = td.seconds // 3600
    minutes = (td.seconds // 60) % 60

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}:{minutes:02d}")
    else:
        parts.append(f"{minutes:02d}")

    return f"{sign}{' '.join(parts)}"


def yield_lines(filepath):
    with open(filepath, "r", encoding="utf8") as f:
        for line in f:
            yield line.strip("\n")


def yield_lines_without_comments(filepath):
    for line in yield_lines(filepath):
        line, *_ = line.split("#", 1)
        line = line.rstrip(" ")
        if line != "":
            yield line
