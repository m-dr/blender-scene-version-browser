import bpy
import traceback

from . import operators, scanner, preferences

# Blender 5.3 collapses the File Browser HEADER region inside real file dialogs
# (so header draw hooks are invisible there) and hides the TOOL_PROPS details
# side-bar by default. The scene list therefore lives in the always-visible
# left TOOLS side-bar, which needs no timers or watchers: Blender keeps that
# region on screen and the user can collapse the panel if vertical space is
# tight (it starts collapsed).


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

    # Controls: Sort (left half) & Single Files (right half)
    sub = layout.split(factor=0.5, align=True)
    row_sort = sub.row(align=True)
    row_sort.prop(settings, "sort_by", text="")
    row_view = sub.row(align=True)
    row_view.prop(settings, "show_unversioned", text="Singles", toggle=True)

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

    col = layout.column(align=True)

    for scene in scenes:
        box = col.box()

        is_expanded = scene["stem"] in operators._expanded_stems
        has_multi = scene["version_count"] > 1

        # Card content: name row, then an info row with the expand chevron on the
        # left, version/size/date (dim) and the magnifier at the right end.
        col_content = box.column(align=True)

        # Name row: scene name
        r1 = col_content.row(align=True)
        r1.alignment = 'LEFT'

        btn_text = f"{scene['name']}  [{scene['latest_version_label']}]" if scene['is_versioned'] else scene['name']
        open_op = r1.operator("svb.open_file", text=btn_text, emboss=False)
        open_op.filename = scene['latest_filename']

        # Info row
        r2 = col_content.row(align=True)

        if has_multi:
            chev_row = r2.row(align=True)
            icon = 'TRIA_DOWN' if is_expanded else 'TRIA_RIGHT'
            exp_op = chev_row.operator("svb.toggle_expand", text="", icon=icon, emboss=False)
            exp_op.stem = scene["stem"]

        info_row = r2.row(align=True)
        info_row.alignment = 'LEFT'
        info_row.active = False

        ver_text = "1 version" if scene["version_count"] == 1 else f"{scene['version_count']} versions"
        info_parts = [ver_text]
        if scene["latest_filesize"]:
            info_parts.append(scene["latest_filesize"])
        if scene["latest_mtime"]:
            info_parts.append(scene["latest_mtime"])

        info_op = info_row.operator("svb.open_file", text=" • ".join(info_parts), emboss=False)
        info_op.filename = scene['latest_filename']

        iso_row = r2.row(align=True)
        iso_row.alignment = 'RIGHT'
        iso_op = iso_row.operator("svb.isolate_scene", text="", icon='VIEWZOOM', emboss=False)
        iso_op.stem = scene["stem"]

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


def _sidebar_location(prefs):
    if prefs is None:
        return 'LEFT'
    return getattr(prefs, "sidebar_location", 'LEFT')


_panel_defaults_applied = False


def _apply_panel_mode_default(prefs):
    """Apply the Collapsed/Expanded default once per session (no timers).

    The collapsible section always uses ``UILayout.panel_prop``: the region-stored
    state of ``UILayout.panel`` makes Blender clip the panel body inside throw-away
    file-dialog screens. ``panel_prop`` keeps the state in the add-on preferences.
    """
    global _panel_defaults_applied
    if _panel_defaults_applied or prefs is None:
        return
    _panel_defaults_applied = True
    state = getattr(prefs, "panel_state", 'COLLAPSED')
    if state == 'COLLAPSED':
        prefs.panel_expanded = False
    elif state == 'EXPANDED':
        prefs.panel_expanded = True


def _draw_sidebar_panel(panel, context):
    """Draw a native collapsible section, honouring the add-on preferences."""
    try:
        layout = panel.layout
        prefs = preferences.get_prefs()
        _apply_panel_mode_default(prefs)

        header = None
        body = None
        if prefs is not None:
            header, body = layout.panel_prop(prefs, "panel_expanded")
        else:
            draw_scenes_ui(layout, context)

        if header is not None:
            header.label(text="Scene Versions (DEV)")

        if body is not None:
            draw_scenes_ui(body, context)
    except Exception:
        traceback.print_exc()
        try:
            panel.layout.label(text="Scene Versions: error (see console)", icon='ERROR')
        except Exception:
            pass


def _draw_with_guard(panel, context):
    """Popover content (the popover has its own Blender-drawn title)."""
    try:
        draw_scenes_ui(panel.layout, context)
    except Exception:
        traceback.print_exc()
        try:
            panel.layout.label(text="Scene Versions: error (see console)", icon='ERROR')
        except Exception:
            pass


class SVB_PT_operator_sidebar(bpy.types.Panel):
    """Scene list in the details sidebar (used when that sidebar is visible)."""
    bl_idname = "SVB_PT_operator_sidebar"
    bl_label = "Scene Versions (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_order = 10
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        location = _sidebar_location(preferences.get_prefs())
        if location == 'LEFT':
            return False
        if location == 'AUTO':
            return _tool_props_visible(context)
        return True

    def draw(self, context):
        _draw_sidebar_panel(self, context)


class SVB_PT_tools_sidebar(bpy.types.Panel):
    """Scene list in the always-visible left sidebar (under Bookmarks/Recent)."""
    bl_idname = "SVB_PT_tools_sidebar"
    bl_label = "Scene Versions (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOLS'
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        location = _sidebar_location(preferences.get_prefs())
        if location == 'RIGHT':
            return False
        if location == 'AUTO':
            return not _tool_props_visible(context)
        return True

    def draw(self, context):
        _draw_sidebar_panel(self, context)


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


def unregister():
    try:
        bpy.types.FILEBROWSER_HT_header.remove(draw_header_button)
    except Exception:
        traceback.print_exc()
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            traceback.print_exc()
