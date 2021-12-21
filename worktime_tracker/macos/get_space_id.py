import subprocess
import time

# Need to import curses before importing Quartz
# https://stackoverflow.com/questions/70327852/bug-when-importing-quartz-before-curses
import curses  # pylint: disable=unused-import
import Quartz

from worktime_tracker.constants import REPO_DIR


def get_wallpaper_filename():
    script_path = REPO_DIR / "worktime_tracker/macos/get_desktop_wallpaper.applescript"
    process = subprocess.run(["/usr/bin/osascript", str(script_path)], capture_output=True, check=False)
    return process.stdout.decode("utf-8").strip()


def get_space_id():
    wallpaper_filename = get_wallpaper_filename()
    while wallpaper_filename == "":
        time.sleep(1)
        print("Error getting wallpaper name.")
        wallpaper_filename = get_wallpaper_filename()
    return wallpaper_filename


def is_screen_locked():
    return Quartz.CGSessionCopyCurrentDictionary().get("CGSSessionScreenIsLocked", 0) == 1
