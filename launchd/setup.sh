#!/bin/bash
cp ~/dev/worktime-tracker/launchd/com.louis.worktimetracker.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.louis.worktimetracker.plist
