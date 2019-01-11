from pathlib import Path
import sys


REPO_DIR = Path(__file__).resolve().parent.parent
LOGS_PATH = REPO_DIR / 'logs.tsv'
LAST_CHECK_PATH = REPO_DIR / 'last_check'


def get_state():
    if sys.platform == 'darwin':
        from worktime_tracker.macos.get_state import get_state
        return get_state()

    raise NotImplementedError('OS {sys.platform} is not supported yet')
