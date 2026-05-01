import sys


if sys.platform == "darwin":
    from worktime_tracker.macos.get_space_id import get_current_space_index, is_screen_locked
elif sys.platform == "win32":
    from worktime_tracker.windows.get_space_id import get_space_id, is_screen_locked
else:
    raise NotImplementedError("OS {sys.platform} is not supported yet")


def get_state():
    if is_screen_locked():
        return "locked"
    if sys.platform == "darwin":
        space_index = get_current_space_index()
        # First space (index 0) is personal, all others are work
        return "personal" if space_index == 0 else "work"
    else:
        # Windows fallback: still uses the old space_types.json approach
        from worktime_tracker.constants import SPACE_TYPES_PATH
        import json
        with open(SPACE_TYPES_PATH, "r", encoding="utf8") as f:
            space_types = json.load(f)
        return space_types[get_space_id()]
