import sys


def start_macos_status_bar_app():
    from worktime_tracker.macos.status_bar import start
    start()


def start_pyqt_gui():
    from worktime_tracker.pyqt_gui import start
    start()


def macos_main():
    print('Starting Worktime Tracker for macOS')
    start_macos_status_bar_app()


def linux_main():
    raise NotImplementedError('Linux not supported yet')
    start_pyqt_gui()  # TODO: There is no get_state() method yet


def windows_main():
    start_pyqt_gui()  # TODO: There is no get_state() method yet


if __name__ == '__main__':
    if sys.platform == 'darwin':
        macos_main()
    elif sys.platform == 'linux':
        linux_main()
    elif sys.platform == 'win32':
        windows_main()
    else:
        raise NotImplementedError(f'OS {sys.platform} is not supported')
