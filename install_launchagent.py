#!/usr/bin/env python3
"""Install or uninstall the Worktime Tracker macOS Launch Agent.

Usage:
    python install_launchagent.py install    # Install and start the Launch Agent
    python install_launchagent.py uninstall  # Stop and remove the Launch Agent
    python install_launchagent.py status     # Check if the Launch Agent is running
    python install_launchagent.py restart    # Restart the Launch Agent

IMPORTANT: Run this script from a regular terminal, NOT from within a sandboxed
application (e.g. Claude Code). macOS blocks LaunchAgent plists written by
sandboxed processes due to provenance tracking.
"""

import os
import subprocess
import sys
from pathlib import Path

LABEL = "com.worktimetracker.worktimetracker"
PLIST_PATH = Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"
PROJECT_DIR = Path(__file__).resolve().parent
LOGS_DIR = PROJECT_DIR / ".logs"
STDOUT_LOG = LOGS_DIR / "launchagent_stdout.log"
STDERR_LOG = LOGS_DIR / "launchagent_stderr.log"


def get_python_executable():
    """Use the Python that's running this script."""
    return sys.executable


def generate_plist():
    python_path = get_python_executable()
    main_script = PROJECT_DIR / "main.py"
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>exec "{python_path}" "{main_script}"</string>
    </array>

    <key>WorkingDirectory</key>
    <string>{PROJECT_DIR}</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>{STDOUT_LOG}</string>

    <key>StandardErrorPath</key>
    <string>{STDERR_LOG}</string>

    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
"""


def is_loaded():
    result = subprocess.run(
        ["launchctl", "list", LABEL],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def _get_uid():
    return os.getuid()


def bootout():
    if is_loaded():
        subprocess.run(
            ["launchctl", "bootout", f"gui/{_get_uid()}", str(PLIST_PATH)],
            capture_output=True,
        )


def bootstrap():
    subprocess.run(
        ["launchctl", "bootstrap", f"gui/{_get_uid()}", str(PLIST_PATH)],
        check=True,
    )


def install():
    LOGS_DIR.mkdir(exist_ok=True)
    plist_content = generate_plist()

    # Unload first if already loaded
    bootout()

    PLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    PLIST_PATH.write_text(plist_content)
    # Remove macOS provenance/quarantine xattrs — launchd refuses to load
    # plists that carry provenance from sandboxed processes.
    subprocess.run(["xattr", "-c", str(PLIST_PATH)], capture_output=True)
    print(f"Wrote plist to {PLIST_PATH}")

    bootstrap()
    print(f"Launch Agent installed and started.")
    print(f"  Python:  {get_python_executable()}")
    print(f"  Project: {PROJECT_DIR}")
    print(f"  Stdout:  {STDOUT_LOG}")
    print(f"  Stderr:  {STDERR_LOG}")
    print(f"\nThe tracker will now start automatically on login and restart if it crashes.")


def uninstall():
    bootout()
    if PLIST_PATH.exists():
        PLIST_PATH.unlink()
        print(f"Removed {PLIST_PATH}")
    else:
        print(f"Plist not found at {PLIST_PATH}")
    print("Launch Agent uninstalled.")


def status():
    if is_loaded():
        result = subprocess.run(
            ["launchctl", "list", LABEL],
            capture_output=True, text=True,
        )
        print(f"Launch Agent is RUNNING")
        print(result.stdout)
    else:
        print(f"Launch Agent is NOT running")
    if PLIST_PATH.exists():
        print(f"Plist exists at {PLIST_PATH}")
    else:
        print(f"No plist found at {PLIST_PATH}")


def restart():
    bootout()
    if PLIST_PATH.exists():
        bootstrap()
        print("Launch Agent restarted.")
    else:
        print("No plist found. Run 'install' first.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("install", "uninstall", "status", "restart"):
        print(__doc__)
        sys.exit(1)

    if sys.platform != "darwin":
        print("This script only works on macOS.")
        sys.exit(1)

    command = sys.argv[1]
    {"install": install, "uninstall": uninstall, "status": status, "restart": restart}[command]()


if __name__ == "__main__":
    main()
