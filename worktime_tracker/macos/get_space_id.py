import subprocess
import time

import Quartz

from worktime_tracker.utils import REPO_DIR


def get_wallpaper_filename():
    script_path = REPO_DIR / 'worktime_tracker/macos/get_desktop_wallpaper.applescript'
    process = subprocess.run(['/usr/bin/osascript', str(script_path)], capture_output=True, check=False)
    return process.stdout.decode('utf-8').strip()


def get_space_id():
    wallpaper_filename = get_wallpaper_filename()
    while wallpaper_filename == '':
        time.sleep(1)
        print('Error getting wallpaper name.')
        wallpaper_filename = get_wallpaper_filename()
    return wallpaper_filename


def is_screen_locked():
    return Quartz.CGSessionCopyCurrentDictionary().get('CGSSessionScreenIsLocked', 0) == 1
