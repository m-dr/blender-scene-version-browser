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

    # Sub-controls
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
        header = box.row(align=True)

        # Expand / collapse chevron for version history
        if scene.version_count > 1:
            icon = 'TRIA_DOWN' if scene.is_expanded else 'TRIA_RIGHT'
            exp_op = header.operator("svb.toggle_expand", text="", icon=icon, emboss=False)
            exp_op.scene_index = idx
        else:
            header.label(text="", icon='FILE_BLEND')

        # Main Open button
        btn_text = f"{scene.name}  [{scene.latest_version_label}]" if scene.is_versioned else scene.name
        open_op = header.operator("svb.open_file", text=btn_text, icon='NONE' if scene.version_count > 1 else 'NONE')
        open_op.filename = scene.latest_filename

        # Quick isolate in grid button
        iso_op = header.operator("svb.isolate_scene", text="", icon='VIEWZOOM', emboss=False)
        iso_op.stem = scene.stem

        # Metadata line
        meta_row = box.row(align=True)
        meta_row.scale_y = 0.8
        info_parts = []
        if scene.version_count > 1:
            info_parts.append(f"{scene.version_count} versions")
        if scene.latest_filesize:
            info_parts.append(scene.latest_filesize)
        if scene.latest_mtime:
            info_parts.append(scene.latest_mtime)

        meta_row.label(text=" • ".join(info_parts))

        # Expanded history list
        if scene.is_expanded and scene.version_count > 1:
            hist_box = box.box().column(align=True)
            hist_box.scale_y = 0.9
            for ver in scene.versions:
                v_row = hist_box.row(align=True)
                is_current_latest = (ver.filename == scene.latest_filename)

                v_label = f"★ {ver.version_label} (Latest)" if is_current_latest else ver.version_label
                v_open = v_row.operator("svb.open_file", text=v_label, icon='FILE_BLEND')
                v_open.filename = ver.filename

                v_row.label(text=f"{ver.size_str}  {ver.mtime_str}")

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
