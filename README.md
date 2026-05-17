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

Install a Launch Agent so the tracker starts on login and restarts if it crashes.

**From a regular Terminal.app** (not from a sandboxed app like Claude Code), run:

```bash
python install_launchagent.py install
```

If the project lives on an encrypted/FUSE volume (e.g. Cryptomator), the install
script may fail due to macOS provenance restrictions. In that case, create the
plist manually:

```bash
mkdir -p ~/.local/log

cat > ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.worktimetracker.worktimetracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>exec PYTHON_PATH PROJECT_DIR/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>HOME/.local/log/worktime-tracker-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>HOME/.local/log/worktime-tracker-stderr.log</string>
    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
EOF

launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
```

Replace `PYTHON_PATH`, `PROJECT_DIR`, and `HOME` with your actual paths.

#### Managing the Launch Agent

```bash
# Check status
launchctl list com.worktimetracker.worktimetracker

# Restart
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist

# Uninstall
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
rm ~/Library/LaunchAgents/com.worktimetracker.worktimetracker.plist
```

Logs: `~/.local/log/worktime-tracker-stdout.log` and `~/.local/log/worktime-tracker-stderr.log`.

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
