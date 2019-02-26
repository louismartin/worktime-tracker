Launchd start of worktime tracker does not work on MacOS Mojave
"Not authorised to send Apple events to System Events"

The problem comes from the fact that `get_desktop_wallpaper.applescript` can't be run with the correct permissions from launchd and python
It works when running directly from the cli: `from worktime_tracker.macos.get_state import get_state; print(get_state())`
It works when running from launchd:
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com.worktimetracker.DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>StandardErrorPath</key>
        <string>/tmp/mycommand.err</string>
        <key>StandardOutPath</key>
        <string>/tmp/mycommand.out</string>
        <key>Label</key>
        <string>com.worktimetracker.worktimetracker</string>
      <key>ProgramArguments</key>
      <array>
      <string>/usr/bin/osascript</string>
        <string>/Users/louismartin/private/dev/worktime-tracker/worktime_tracker/macos/get_desktop_wallpaper.temp.applescript</string>
      </array>
    <key>StartInterval</key>
<integer>1</integer>
    </dict>
</plist>
```
(`watch -n0.1 head /tmp/mycommand.*`)
It does not work when running from python from launchd:
```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com.worktimetracker.DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>StandardErrorPath</key>
        <string>/tmp/mycommand.err</string>
        <key>StandardOutPath</key>
        <string>/tmp/mycommand.out</string>
<key>UserName</key>
<string>louismartin</string>
        <key>Label</key>
        <string>com.worktimetracker.worktimetracker</string>
      <key>ProgramArguments</key>
      <array>
      <string>/Users/louismartin/miniconda3/bin/python</string>
        <string>/Users/louismartin/private/dev/worktime-tracker/main.py</string>
      </array>
    <key>StartInterval</key>
<integer>1</integer>
    </dict>
</plist>
```
