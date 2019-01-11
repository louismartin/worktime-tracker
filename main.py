import sys


def macos_main():
    from worktime_tracker.mac_status_bar_gui import WorktimeTrackerStatusBarApp
    print('Starting Worktime Tracker for macOS')
    WorktimeTrackerStatusBarApp().run()


def linux_main():
    raise NotImplementedError('Linux not supported yet')


def windows_main():
    raise NotImplementedError('Windows not supported yet')


if __name__ == '__main__':
    if sys.platform == 'darwin':
        macos_main()
    elif sys.platform == 'linux':
        linux_main()
    elif sys.platform == 'win32':
        windows_main()
    else:
        raise NotImplementedError(f'OS {sys.platform} is not supported')
