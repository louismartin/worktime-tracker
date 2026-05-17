# Worktime Tracker

Tool to track work time during the day using multiple desktops/workspaces on macOS.

The first Space (index 0) is treated as "personal", all others as "work". Screen lock is detected as "locked".

## Getting Started

### Requirements

- macOS
- Python >= 3.8
- Multiple macOS Spaces (desktops) configured

### Installing

Clone the repository, cd into it, and install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements_macos.txt
```

### Running manually

```bash
python main.py
```

### Running automatically (recommended)

Install the Launch Agent so the tracker starts on login and restarts if it crashes.
**Important:** Run this from a regular terminal, not from a sandboxed app (e.g. Claude Code),
because macOS blocks LaunchAgent plists written by sandboxed processes.

```bash
python install_launchagent.py install
```

Other commands:
```bash
python install_launchagent.py status    # Check if running
python install_launchagent.py restart   # Restart the agent
python install_launchagent.py uninstall # Stop and remove the agent
```

Logs are written to `~/.local/log/worktime-tracker-stdout.log` and `~/.local/log/worktime-tracker-stderr.log`.

### Configuration

Edit `config.json` to change settings:
```json
{
    "interface": "macos-status-bar",
    "show_day_worktime": true
}
```

Available interfaces: `cli`, `cli-curses`, `macos-status-bar`.

### Tests

```bash
pytest tests/
```
