import subprocess

import Quartz

from worktime_tracker.utils import REPO_DIR


def get_space_id():
    script_path = REPO_DIR / 'worktime_tracker/macos/get_desktop_wallpaper.applescript'
    process = subprocess.run(['/usr/bin/osascript', str(script_path)], capture_output=True, check=False)
    wallpaper_filename = process.stdout.decode('utf-8').strip()
    return wallpaper_filename


def is_screen_locked():
    return Quartz.CGSessionCopyCurrentDictionary().get('CGSSessionScreenIsLocked', 0) == 1


