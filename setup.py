#!/usr/bin/env python
from pathlib import Path
import subprocess
import sys

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def setup_macos():
    python_executable_path = sys.executable
    worktime_tracker_main_script_path = Path(__file__).resolve().parent / 'main.py'
    plist = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com.worktimetracker.DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.worktimetracker.worktimetracker</string>
        <key>ProgramArguments</key>
        <array>
            <string>{python_executable_path}</string>
            <string>{worktime_tracker_main_script_path}</string>
        </array>
        <key>KeepAlive</key>
        <true/>
    </dict>
</plist>\n'''
    destination_plist_path = Path.home() / 'Library/LaunchAgents/com.worktimetracker.worktimetracker.plist'
    with destination_plist_path.open('w') as f:
        f.write(plist)
    subprocess.run(['launchctl', 'load', destination_plist_path], check=True)


def custom_setup():
    if sys.platform == 'darwin':
        setup_macos()


class PostDevelopCommand(develop):
    """Post-installation for development mode."""
    def run(self):
        custom_setup()
        develop.run(self)


class PostInstallCommand(install):
    """Post-installation for installation mode."""
    def run(self):
        custom_setup()
        install.run(self)


setup(
    name='worktime_tracker',
    version='0.1',
    description='Worktime Tracker',
    author='Louis Martin',
    author_email='louisrtm@gmail.com',
    packages=['worktime_tracker'],
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
)
