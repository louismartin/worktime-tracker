#!/usr/bin/env python
import sys

from worktime_tracker.config import Config


def start_macos_status_bar_app():
    from worktime_tracker.macos.status_bar import start

    start()


def start_cli():
    from worktime_tracker.cli import start

    start()


def start_cli_curses():
    from worktime_tracker.cli_curses import start

    start()


INTERFACES = {
    "cli": start_cli,
    "cli-curses": start_cli_curses,
    "macos-status-bar": start_macos_status_bar_app,
}


def main():
    if sys.platform != "darwin":
        raise NotImplementedError(f"OS {sys.platform} is not supported")
    interface = Config().interface
    print(f"Starting Worktime Tracker (interface={interface})")
    INTERFACES[interface]()


if __name__ == "__main__":
    main()
