import ctypes
from functools import lru_cache

import win32gui

from worktime_tracker.utils import REPO_DIR


@lru_cache(maxsize=1)
def get_virtual_desktop_accessor():
    # See https://github.com/Ciantic/VirtualDesktopAccessor/blob/master/x64/Release/VirtualDesktopAccessor.dll
    return ctypes.WinDLL(str(REPO_DIR / 'worktime_tracker/windows/VirtualDesktopAccessor.dll'))


def get_desktop_number():
    return get_virtual_desktop_accessor().GetCurrentDesktopNumber()


def is_screen_locked():
    return win32gui.GetWindowText(get_virtual_desktop_accessor().ViewGetFocused()) == ''


def get_space_id():
    return str(get_desktop_number())
