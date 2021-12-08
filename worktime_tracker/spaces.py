from functools import lru_cache
import json
import sys

from worktime_tracker.utils import SPACE_TYPES_PATH


if sys.platform == 'darwin':
    from worktime_tracker.macos.get_space_id import get_space_id, is_screen_locked
elif sys.platform == 'win32':
    from worktime_tracker.windows.get_space_id import get_space_id, is_screen_locked
else:
    raise NotImplementedError('OS {sys.platform} is not supported yet')


@lru_cache(maxsize=1)
def get_space_types():
    with open(SPACE_TYPES_PATH, 'r', encoding='utf8') as f:
        return json.load(f)


def get_state():
    if is_screen_locked():
        return 'locked'
    return get_space_types()[get_space_id()]
