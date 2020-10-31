import sys
import time
import json

from worktime_tracker.spaces import get_space_id
from worktime_tracker.utils import SPACE_TYPES_PATH


def setup_spaces(get_space_id):
    if SPACE_TYPES_PATH.exists():
        return
    print('Welcome to WorktimeTracker. In order for the tool to work, you need to create multiple spaces.\n'
          'Please go into each of your spaces and indicate whether it is a "Work" or a "Personal" space')
    spaces = {}
    time.sleep(3)
    try:
        while True:
            space_id = get_space_id()
            if space_id in spaces:
                print(f'Move to another workspace or hit ctrl-c to finish (current: {space_id}).')
                time.sleep(3)
                continue
            answer = input(f'{space_id}: Is this a "Work" or a "Personal" space? (w/p): ').lower()
            assert answer in ['w', 'p']
            space_type = {'w': 'work', 'p': 'personal'}[answer]
            print(f'Writing that {space_id} is a {space_type} space.')
            spaces[space_id] = space_type
    except KeyboardInterrupt:
        print(f'Writing spaces to {SPACE_TYPES_PATH}')
    with open(SPACE_TYPES_PATH, 'w') as f:
        json.dump(spaces, f)


def start_macos_status_bar_app():
    from worktime_tracker.macos.status_bar import start
    start()


def start_pyqt_gui():
    from worktime_tracker.pyqt_gui import start
    start()


def start_cli():
    from worktime_tracker.cli.cli import start
    start()


def macos_main():
    print('Starting Worktime Tracker for macOS')
    start_macos_status_bar_app()


def linux_main():
    raise NotImplementedError('Linux not supported yet')
    start_pyqt_gui()  # TODO: There is no get_state() method yet


def windows_main():
    start_pyqt_gui()


if __name__ == '__main__':
    if sys.platform == 'darwin':
        main = macos_main
    elif sys.platform == 'linux':
        main = linux_main
    elif sys.platform == 'win32':
        main = windows_main
    else:
        raise NotImplementedError(f'OS {sys.platform} is not supported')
    setup_spaces(get_space_id)
    main()
