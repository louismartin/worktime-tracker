import time
import shutil

from worktime_tracker.utils import LOGS_PATH, LAST_CHECK_PATH, reverse_read_lines


ALL_LOGS = []


def write_last_check(timestamp):
    with LAST_CHECK_PATH.open('w') as f:
        f.write(str(timestamp) + '\n')


def read_last_check_timestamp():
    if not LAST_CHECK_PATH.exists():
        with open(LAST_CHECK_PATH, 'w', encoding='utf8') as f:
            f.write('0\n')
    with LAST_CHECK_PATH.open('r') as f:
        return float(f.readline().strip())


def write_log(timestamp, state):
    with LOGS_PATH.open('a') as f:
        f.write(f'{timestamp}\t{state}\n')


def maybe_write_log(timestamp, state):
    # TODO: lock file
    _, last_state = read_last_log()
    if last_state == state:
        return
    write_log(timestamp, state)


def parse_log_line(log_line):
    timestamp, state = log_line.strip().split('\t')
    return float(timestamp), state


def reverse_read_logs():
    if not LOGS_PATH.exists():
        LOGS_PATH.parent.mkdir(exist_ok=True)
        write_log(timestamp=0, state='locked')
    for line in reverse_read_lines(LOGS_PATH):
        yield parse_log_line(line)


def get_all_logs():
    # We don't reload all logs each time, just the new ones
    last_timestamp = 0
    if len(ALL_LOGS) > 0:
        last_timestamp, _ = ALL_LOGS[-1]  # Last loaded log
    new_logs = []
    # Read file in reverse to find new logs that are not loaded yet
    for timestamp, state in reverse_read_logs():
        if timestamp <= last_timestamp:
            break
        new_logs.append((timestamp, state))
    ALL_LOGS.extend(new_logs[::-1])
    return ALL_LOGS.copy()


def get_logs(start_timestamp, end_timestamp):
    end_timestamp = min(end_timestamp, time.time())
    logs = [(end_timestamp, 'locked')]  # Add a virtual state at the end of the logs to count the last state
    for timestamp, state in get_all_logs()[::-1]:  # Read the logs backward
        if timestamp > end_timestamp:
            continue
        if timestamp < start_timestamp:
            logs.append((start_timestamp, state))  # The first log will be dated at the start timestamp queried
            break
        logs.append((timestamp, state))
    return logs[::-1]  # Order the list back to original because we have read the logs backward


def read_last_log():
    try:
        return next(reverse_read_logs())
    except StopIteration:
        return None


def read_first_log():
    with open(LOGS_PATH, 'r', encoding='utf8') as f:
        try:
            first_line = next(f)
        except StopIteration:
            return None
        return parse_log_line(first_line)


def get_rewritten_history_logs(start_timestamp, end_timestamp, new_state, logs):
    assert end_timestamp < logs[-1][0], 'Rewriting the future not allowed'
    # Remove logs that are in the interval to be rewritten
    logs_before = [(timestamp, state) for (timestamp, state) in logs if timestamp <= start_timestamp]
    logs_after = [(timestamp, state) for (timestamp, state) in logs if timestamp > end_timestamp]
    logs_inside = [
        (timestamp, state) for (timestamp, state) in logs if start_timestamp < timestamp and timestamp <= end_timestamp
    ]
    if len(logs_inside) > 0:
        # Push back last log inside to be the first of logs after (the rewritten history needs to end on the same
        # state as it was actually recorded)
        logs_after = [(end_timestamp, logs_inside[-1][1])] + logs_after
    else:
        # If there were no states inside, then just take the last log before to have the same state
        logs_after = [(end_timestamp, logs_before[-1][1])] + logs_after
    # Edge cases to not have two identical subsequent states
    if logs_before[-1][1] == new_state:
        # Change the start date to the previous one if it is the same state
        start_timestamp = logs_before[-1][0]
        logs_before = logs_before[:-1]
    if logs_after[0][1] == new_state:
        # Remove first element if it is the same as the one we are going to introduce
        logs_after = logs_after[1:]
    return logs_before + [(start_timestamp, new_state)] + logs_after


def rewrite_history(start_timestamp, end_timestamp, new_state):
    # Careful, this methods rewrites the entire log file
    shutil.copy(LOGS_PATH, f'{LOGS_PATH}.bck{int(time.time())}')
    with LOGS_PATH.open('r') as f:
        logs = get_logs(start_timestamp=0, end_timestamp=time.time())
    new_logs = get_rewritten_history_logs(start_timestamp, end_timestamp, new_state, logs)
    with LOGS_PATH.open('w') as f:
        for timestamp, state in new_logs:
            f.write(f'{timestamp}\t{state}\n')
    ALL_LOGS[:] = []  # Reset logs
