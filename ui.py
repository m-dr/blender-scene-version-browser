import bpy
from . import operators


def draw_scenes_ui(layout, context):
    wm = context.window_manager
    settings = wm.svb_settings
    scenes = wm.svb_scenes

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

    if not scenes:
        box = layout.box()
        box.label(text="No .blend scenes detected", icon='INFO')
        box.operator("svb.refresh", text="Scan Directory", icon='FILE_REFRESH')
        return

    filter_text = settings.search_query.strip().lower()

    # List of scenes
    col = layout.column(align=True)
    visible_count = 0

    for idx, scene in enumerate(scenes):
        if filter_text and filter_text not in scene.name.lower():
            continue

        visible_count += 1
        box = col.box()
        main_row = box.row(align=True)

        # 1. Left column: Chevron (for multi-version) or BLANK1 spacer (for single version)
        col_chev = main_row.column(align=True)
        if scene.version_count > 1:
            icon = 'TRIA_DOWN' if scene.is_expanded else 'TRIA_RIGHT'
            exp_op = col_chev.operator("svb.toggle_expand", text="", icon=icon, emboss=False)
            exp_op.scene_index = idx
        else:
            col_chev.label(text="", icon='BLANK1')

        # 2. Content column: Contains BOTH the scene name and the info row in the exact same column
        col_body = main_row.column(align=True)

        # Primary scene name row (prominent, full brightness)
        r_name = col_body.row(align=True)
        r_name.alignment = 'LEFT'
        btn_text = f"{scene.name}  [{scene.latest_version_label}]" if scene.is_versioned else scene.name
        open_op = r_name.operator("svb.open_file", text=btn_text, emboss=False)
        open_op.filename = scene.latest_filename

        # Secondary info row (subdued/fainter via active=False, slightly more compact)
        r_info = col_body.row(align=True)
        r_info.alignment = 'LEFT'
        r_info.active = False
        r_info.scale_y = 0.82

        ver_text = "1 version" if scene.version_count == 1 else f"{scene.version_count} versions"
        info_parts = [ver_text]
        if scene.latest_filesize:
            info_parts.append(scene.latest_filesize)
        if scene.latest_mtime:
            info_parts.append(scene.latest_mtime)

        r_info.label(text=" • ".join(info_parts))

        # 3. Right column: Quick isolate in grid button
        col_zoom = main_row.column(align=True)
        col_zoom.alignment = 'RIGHT'
        iso_op = col_zoom.operator("svb.isolate_scene", text="", icon='VIEWZOOM', emboss=False)
        iso_op.stem = scene.stem

        # Expanded history list
        if scene.is_expanded and scene.version_count > 1:
            hist_box = box.box().column(align=True)
            hist_box.scale_y = 0.9
            for ver in scene.versions:
                v_row = hist_box.row(align=True)
                v_left = v_row.row(align=True)
                v_left.alignment = 'LEFT'

                is_current_latest = (ver.filename == scene.latest_filename)
                v_label = f"★ {ver.version_label} (Latest)" if is_current_latest else ver.version_label
                v_open = v_left.operator("svb.open_file", text=v_label, emboss=False)
                v_open.filename = ver.filename

                v_right = v_row.row(align=True)
                v_right.alignment = 'RIGHT'
                v_right.active = False
                v_right.label(text=f"{ver.size_str}  {ver.mtime_str}")

    if visible_count == 0 and scenes:
        layout.label(text="No scenes match filter", icon='INFO')


class SVB_PT_operator_sidebar(bpy.types.Panel):
    """Panel injected into the right sidebar (TOOL_PROPS) of file dialogs (File > Open, Link, Append)."""
    bl_idname = "SVB_PT_operator_sidebar"
    bl_label = "Scene Versions (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_order = 10

    def draw(self, context):
        draw_scenes_ui(self.layout, context)


class SVB_PT_header_popover(bpy.types.Panel):
    """Header popover button for standalone File Browser editors."""
    bl_idname = "SVB_PT_header_popover"
    bl_label = "Scenes (DEV)"
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'HEADER'
    bl_ui_units_x = 22

    def draw(self, context):
        draw_scenes_ui(self.layout, context)


def draw_header_button(self, context):
    """Draw popover trigger in File Browser header next to filter."""
    space = getattr(context, "space_data", None)
    if space and getattr(space, "browse_mode", 'FILES') == 'FILES':
        self.layout.popover(panel="SVB_PT_header_popover", text="Scenes", icon='FILE_BLEND')


classes = (
    SVB_PT_operator_sidebar,
    SVB_PT_header_popover,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.FILEBROWSER_HT_header.append(draw_header_button)


def unregister():
    bpy.types.FILEBROWSER_HT_header.remove(draw_header_button)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
