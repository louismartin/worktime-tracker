import ctypes

import Quartz
import objc


def _get_cgs_lib():
    lib = ctypes.CDLL("/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices")
    lib.CGSMainConnectionID.restype = ctypes.c_int
    lib.CGSCopyManagedDisplaySpaces.restype = ctypes.c_void_p
    lib.CGSCopyManagedDisplaySpaces.argtypes = [ctypes.c_int]
    lib.CGDisplayCreateUUIDFromDisplayID.restype = ctypes.c_void_p
    lib.CGDisplayCreateUUIDFromDisplayID.argtypes = [ctypes.c_uint32]
    return lib


_lib = _get_cgs_lib()


def _get_builtin_display_uuids():
    """Return the set of Display Identifier UUIDs that are built-in screens."""
    from CoreFoundation import CFUUIDCreateString

    builtin_uuids = set()
    (err, display_ids, count) = Quartz.CGGetOnlineDisplayList(10, None, None)
    for i in range(count):
        did = display_ids[i]
        if Quartz.CGDisplayIsBuiltin(did):
            uuid_ref = _lib.CGDisplayCreateUUIDFromDisplayID(did)
            uuid_obj = objc.objc_object(c_void_p=ctypes.c_void_p(uuid_ref))
            uuid_str = str(CFUUIDCreateString(None, uuid_obj))
            builtin_uuids.add(uuid_str)
    return builtin_uuids


def get_current_space_index():
    """Return the 0-based index of the current space on the relevant display.

    When multiple displays are connected, the external display is used.
    When only one display is connected, that display is used.
    """
    conn = _lib.CGSMainConnectionID()
    spaces_ptr = _lib.CGSCopyManagedDisplaySpaces(conn)
    displays = objc.objc_object(c_void_p=ctypes.c_void_p(spaces_ptr))

    if len(displays) == 1:
        display = displays[0]
    else:
        # Multiple displays: pick the external one (non-built-in)
        builtin_uuids = _get_builtin_display_uuids()
        display = None
        for d in displays:
            if d["Display Identifier"] not in builtin_uuids:
                display = d
                break
        if display is None:
            # Fallback: use the first display
            display = displays[0]

    current_space_id = display["Current Space"]["ManagedSpaceID"]
    spaces = display["Spaces"]
    for idx, space in enumerate(spaces):
        if space["ManagedSpaceID"] == current_space_id:
            return idx
    return 0


def get_space_id():
    """Return the space ID used by the rest of the app.

    Returns the 0-based space index as a string.
    """
    return get_current_space_index()


def is_screen_locked():
    session = Quartz.CGSessionCopyCurrentDictionary()
    if session is None:
        return True
    return session.get("CGSSessionScreenIsLocked", 0) == 1
