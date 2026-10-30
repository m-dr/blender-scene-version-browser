import bpy
from . import operators, preferences

_timer_running = False
_known_dialog_spaces = set()


def _ensure_sidebar_visible():
    prefs = preferences.get_prefs()
    if prefs and not prefs.auto_open_options:
        return

    live_spaces = set()
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'FILE_BROWSER':
                continue
            space = area.spaces.active
            if not space or space.active_operator is None:
                continue

            key = space.as_pointer()
            live_spaces.add(key)

            if key not in _known_dialog_spaces:
                _known_dialog_spaces.add(key)
                if not space.show_region_tool_props:
                    space.show_region_tool_props = True
                    area.tag_redraw()

    # Clean up closed dialog references
    _known_dialog_spaces.intersection_update(live_spaces)


def poll_file_browsers():
    try:
        wm = bpy.context.window_manager
    except (AttributeError, RuntimeError):
        return 0.5

    # 1. Automatically expand options sidebar in operator dialogs
    _ensure_sidebar_visible()

    # 2. Check if auto refresh is enabled
    settings = getattr(wm, "svb_settings", None)
    if not settings or not settings.auto_refresh:
        prefs = preferences.get_prefs()
        return prefs.poll_interval if prefs else 0.5

    # 3. Detect directory change
    for window in wm.windows:
        for area in window.screen.areas:
            if area.type != 'FILE_BROWSER':
                continue
            space = area.spaces.active
            if not space or not space.params or getattr(space, "browse_mode", 'FILES') != 'FILES':
                continue

            directory = space.params.directory
            if isinstance(directory, bytes):
                directory = directory.decode("utf-8", "replace")

            if directory and directory != wm.svb_current_dir:
                operators.rebuild_scenes(wm, directory)
                area.tag_redraw()
            break

    prefs = preferences.get_prefs()
    return prefs.poll_interval if prefs else 0.5


def register():
    global _timer_running
    if not _timer_running:
        if not bpy.app.timers.is_registered(poll_file_browsers):
            bpy.app.timers.register(poll_file_browsers, first_interval=0.5, persistent=True)
        _timer_running = True


def unregister():
    global _timer_running
    if bpy.app.timers.is_registered(poll_file_browsers):
        bpy.app.timers.unregister(poll_file_browsers)
    _timer_running = False
    _known_dialog_spaces.clear()
