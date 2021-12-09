# Worktime Tracker

Tool to track work time during the day using multiple desktops/workspaces on macOS (and soon Windows).

## Getting Started

### Requirements

Python >= 3.6

### Installing

Clone the repository, cd into it and install with:
```bash
pip setup.py install
```

### macOS

Activate and deactivate launchd with
```bash
launchctl load ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
launchctl unload ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
```

### Running

Run with:
```bash
python main.py
```


TODO: Add screenshot of plots