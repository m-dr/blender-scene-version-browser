import bpy
import traceback

from . import operators, scanner, preferences

# Blender 5.3 layout changes: in a real "File > Open" dialog the File Browser
# HEADER region is collapsed (so header draw hooks are invisible) and the
# TOOL_PROPS side-bar region is hidden by default (`show_region_tool_props`
# False). Both regions are required by this add-on, so track which file
# browsers have already been visited and reveal the details region once for
# each - a later manual collapse is respected.
_seen_filebrowsers = set()


def _iter_filebrowser_spaces():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'FILE_BROWSER':
                continue
            for space in area.spaces:
                if space.type == 'FILE_BROWSER':
                    yield window, area, space


def _ensure_sidebar_region():
    """Reveal the File Browser details region the scene list lives in (Blender 5.3)."""
    try:
        live_keys = set()
        for window, area, space in list(_iter_filebrowser_spaces()):
            key = (window.as_pointer(), area.as_pointer())
            live_keys.add(key)
            if key in _seen_filebrowsers:
                continue
            _seen_filebrowsers.add(key)
            if getattr(space, "browse_mode", "FILES") != "FILES":
                continue
            if getattr(space, "show_region_tool_props", True) is False:
                try:
                    space.show_region_tool_props = True
                    area.tag_redraw()
                except Exception:
                    traceback.print_exc()
        _seen_filebrowsers.intersection_update(live_keys)
    except Exception:
        traceback.print_exc()
    return 0.5


def _tool_props_visible(context):
    area = getattr(context, "area", None)
    if area is None:
        return False
    for region in area.regions:
        if region.type == 'TOOL_PROPS' and region.width > 1:
            return True
    return False


def draw_scenes_ui(layout, context):
    dirpath = operators.get_current_directory(context)
    wm = context.window_manager
    settings = wm.svb_settings
    prefs = preferences.get_prefs()
    include_blend1 = prefs.include_blend1 if prefs else False

    # Top control bar
    row = layout.row(align=True)
    row.prop(settings, "search_query", text="", icon='VIEWZOOM', placeholder="Filter scenes...")
    row.operator("svb.refresh", text="", icon='FILE_REFRESH')

    # Sub-controls: Sort & Single Files
    sub = layout.row(align=True)
    sub.prop(settings, "sort_by", text="")
    sub.prop(settings, "show_unversioned", text="Singles", toggle=True)

    # Main view search clear if filtered
    space = operators.active_file_space(context)
    if space and space.params and space.params.filter_search:
        clear_row = layout.row()
        clear_row.alert = True
        clear_row.operator("svb.clear_isolation", text="Reset Grid Filter", icon='X')

    if not dirpath:
        box = layout.box()
        box.label(text="No active directory", icon='INFO')
        return

    scenes = scanner.get_scenes(
        dirpath,
        show_unversioned=settings.show_unversioned,
        include_blend1=include_blend1,
        sort_by=settings.sort_by,
    )

    if not scenes:
        box = layout.box()
        box.label(text="No .blend scenes detected", icon='INFO')
        box.operator("svb.refresh", text="Scan Directory", icon='FILE_REFRESH')
        return

    filter_text = settings.search_query.strip().lower()

    col = layout.column(align=True)
    visible_count = 0

    for scene in scenes:
        if filter_text and filter_text not in scene["name"].lower():
            continue

        visible_count += 1
        box = col.box()

        is_expanded = scene["stem"] in operators._expanded_stems
        has_multi = scene["version_count"] > 1

        # Card container row:
        # col_toggle (fixed width chevron/spacer) + col_content (name/zoom + info)
        card_row = box.row()

        # 1. Left toggle / spacer column
        col_toggle = card_row.column(align=True)
        if has_multi:
            icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
            exp_op = col_toggle.operator("svb.toggle_expand", text="", icon=icon, emboss=False)
            exp_op.stem = scene["stem"]
        else:
            dummy_op = col_toggle.operator("svb.toggle_expand", text="", icon='BLANK1', emboss=False)
            dummy_op.stem = ""

        # 2. Main content column: scene name row + info row
        col_content = card_row.column(align=True)

        # Header row: Scene name (left) + Magnifying glass (right)
        r1 = col_content.row()
        r1_left = r1.row(align=True)
        r1_left.alignment = 'LEFT'

        btn_text = f"{scene['name']}  [{scene['latest_version_label']}]" if scene['is_versioned'] else scene['name']
        open_op = r1_left.operator("svb.open_file", text=btn_text, emboss=False)
        open_op.filename = scene['latest_filename']

        r1_right = r1.row(align=True)
        r1_right.alignment = 'RIGHT'
        iso_op = r1_right.operator("svb.isolate_scene", text="", icon='VIEWZOOM', emboss=False)
        iso_op.stem = scene["stem"]

        # Details row: Info chunks (aligned exactly with scene name, dimmer theme color)
        r2 = col_content.row(align=True)
        r2.alignment = 'LEFT'
        r2.active = False
        r2.scale_y = 0.82

        ver_text = "1 version" if scene["version_count"] == 1 else f"{scene['version_count']} versions"
        info_parts = [ver_text]
        if scene["latest_filesize"]:
            info_parts.append(scene["latest_filesize"])
        if scene["latest_mtime"]:
            info_parts.append(scene["latest_mtime"])

        info_op = r2.operator("svb.open_file", text=" • ".join(info_parts), emboss=False)
        info_op.filename = scene['latest_filename']

        # 3. Expanded history list
        if is_expanded and has_multi:
            hist_box = box.box().column(align=True)
            hist_box.scale_y = 0.9
            for ver in scene["versions"]:
                v_row = hist_box.row()
                v_left = v_row.row(align=True)
                v_left.alignment = 'LEFT'

                is_current_latest = (ver["filename"] == scene["latest_filename"])
                v_label = f"★ {ver['version_label']} (Latest)" if is_current_latest else ver["version_label"]
                v_open = v_left.operator("svb.open_file", text=v_label, emboss=False)
                v_open.filename = ver["filename"]

                v_right = v_row.row(align=True)
                v_right.alignment = 'RIGHT'
                v_right.active = False
                v_right.label(text=f"{ver['size_str']}  {ver['mtime_str']}")

    if visible_count == 0 and scenes:
        layout.label(text="No scenes match filter", icon='INFO')


def _draw_with_guard(panel, context):
    try:
        draw_scenes_ui(panel.layout, context)
    except Exception:
        traceback.print_exc()
        try:
            panel.layout.label(text="Scene Versions: error (see console)", icon='ERROR')
        except Exception:
            pass


class SVB_PT_operator_sidebar(bpy.types.Panel):
    """Panel injected into the right sidebar (TOOL_PROPS) of file dialogs (File > Open, Link, Append)."""
    bl_idname = "SVB_PT_operator_sidebar"
    bl_label = "Scene Versions (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_order = 10

    def draw(self, context):
        _draw_with_guard(self, context)


class SVB_PT_tools_sidebar(bpy.types.Panel):
    """Fallback in the always-visible left sidebar when the details region is hidden.

    Blender 5.3 hides the File Browser's TOOL_PROPS (details) region by default;
    this panel makes the scene list reachable even then (e.g. after the user
    closes the details side-bar).
    """
    bl_idname = "SVB_PT_tools_sidebar"
    bl_label = "Scene Versions (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return not _tool_props_visible(context)

    def draw(self, context):
        _draw_with_guard(self, context)


class SVB_PT_header_popover(bpy.types.Panel):
    """Header popover button for standalone File Browser editors."""
    bl_idname = "SVB_PT_header_popover"
    bl_label = "Scenes (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 22

    def draw(self, context):
        _draw_with_guard(self, context)


def draw_header_button(self, context):
    """Draw popover trigger in File Browser header next to filter."""
    try:
        space = getattr(context, "space_data", None)
        if space and getattr(space, "browse_mode", 'FILES') == 'FILES':
            self.layout.popover(panel="SVB_PT_header_popover", text="Scenes", icon='FILE_BLEND')
    except Exception:
        traceback.print_exc()


classes = (
    SVB_PT_operator_sidebar,
    SVB_PT_tools_sidebar,
    SVB_PT_header_popover,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.FILEBROWSER_HT_header.append(draw_header_button)
    if not bpy.app.timers.is_registered(_ensure_sidebar_region):
        bpy.app.timers.register(_ensure_sidebar_region, first_interval=0.25, persistent=True)


def unregister():
    if bpy.app.timers.is_registered(_ensure_sidebar_region):
        try:
            bpy.app.timers.unregister(_ensure_sidebar_region)
        except Exception:
            pass
    try:
        bpy.types.FILEBROWSER_HT_header.remove(draw_header_button)
    except Exception:
        traceback.print_exc()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            traceback.print_exc()
