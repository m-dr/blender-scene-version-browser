import bpy
from . import operators, scanner, preferences


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
        info_op.filename = scene["latest_filename"]

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
