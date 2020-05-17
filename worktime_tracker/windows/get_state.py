import ctypes
import win32gui

virtual_desktop_accessor = ctypes.WinDLL(r'worktime_tracker\windows\VirtualDesktopAccessor-master\x64\Release\VirtualDesktopAccessor.dll')

def get_desktop_number():
    return virtual_desktop_accessor.GetCurrentDesktopNumber()


def is_screen_locked():
    return win32gui.GetWindowText(virtual_desktop_accessor.ViewGetFocused()) == ''


def get_state():
    desktop_number = get_desktop_number()
    if is_screen_locked():
        return 'idle'
    # Change to your mapping of desktops to state
    if desktop_number == 0:
        return 'work'
    if desktop_number == 1:
        return 'leisure'
    raise