from pathlib import Path


REPO_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_DIR / ".logs/"
LOGS_PATH = LOGS_DIR / "logs.tsv"
LAST_CHECK_PATH = LOGS_DIR / ".last_check.txt"
SPACE_TYPES_PATH = REPO_DIR / "space_types.json"
LOGS_DIR.mkdir(exist_ok=True)
DAY_START_HOUR = 7  # Hour at which the day starts
STATES = ["work", "personal", "locked"]
WORK_STATES = ["work"]
REFRESH_RATE = 30
