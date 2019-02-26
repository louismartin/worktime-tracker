import subprocess

import Quartz

from worktime_tracker.utils import REPO_DIR


def get_desktop_number():
    script_path = REPO_DIR / 'worktime_tracker/macos/get_desktop_wallpaper.applescript'
    process = subprocess.run(['/usr/bin/osascript', str(script_path)], capture_output=True, check=False)
    wallpaper_filename = process.stdout.decode('utf-8').strip()
    return {
        # Change to your wallpaper filenames
        'Facebook_Backgrounds--node_facebook (1).png': 1,
        'Facebook_Backgrounds--friendsgc.png': 2,
        'DefaultDesktop.heic': 3,
    }[wallpaper_filename]


def is_screen_locked():
    return Quartz.CGSessionCopyCurrentDictionary().get('CGSSessionScreenIsLocked', 0) == 1


def get_state():
    desktop_number = get_desktop_number()
    if is_screen_locked():
        return 'idle'
    # Change to your mapping of desktops to state
    if desktop_number == 1:
        return 'work'
    if desktop_number == 2:
        return 'email'
    if desktop_number == 3:
        return 'leisure'
    raise
