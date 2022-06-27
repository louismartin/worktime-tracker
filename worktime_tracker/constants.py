from pathlib import Path
from typing import Literal


REPO_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_DIR / ".logs/"
LOGS_PATH = LOGS_DIR / "logs.tsv"
DAYS_OFF_PATH = LOGS_DIR / "days_off.tsv"
DONT_COUNT_DAYS_PATH = LOGS_DIR / "dont_count_days.tsv"
LAST_CHECK_PATH = LOGS_DIR / "last_check.txt"
SPACE_TYPES_PATH = REPO_DIR / "space_types.json"
LOGS_DIR.mkdir(exist_ok=True)
STATES = ["work", "personal", "locked"]
STATES_TYPE = Literal["work", "personal", "locked"]  # TODO: Find syntax to make STATES_TYPE use the values in STATES (Literal[STATES] or Literal[*STATES] don't work)
WORK_STATES = ["work"]
REFRESH_RATE = 30
