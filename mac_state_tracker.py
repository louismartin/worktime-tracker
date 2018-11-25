import time
from pathlib import Path
import subprocess

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


def write_state(state):
    log_path = repo_dir / 'log.txt'
    with log_path.open('a') as f:
        f.write(f'{time.time()}\t{state}\n')


if __name__ == '__main__':
    last_state = None
    while True:
        state = get_state()
        if state != last_state:
            print(state)
            write_state(state)
            last_state = state
    time.sleep(0.1)
