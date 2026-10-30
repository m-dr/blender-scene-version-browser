import os
import bpy
from bpy.props import IntProperty, StringProperty
from . import scanner, preferences


def active_file_space(context=None):
    """Return the active File Browser space if current context or any window has one."""
    if context:
        space = getattr(context, "space_data", None)
        if space and space.type == 'FILE_BROWSER' and space.params:
            if getattr(space, "browse_mode", 'FILES') == 'FILES':
                return space

    # Fallback to inspecting open windows
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'FILE_BROWSER':
                sp = area.spaces.active
                if sp and sp.params and getattr(sp, "browse_mode", 'FILES') == 'FILES':
                    return sp
    return None


def get_current_directory(context=None) -> str:
    space = active_file_space(context)
    if space and space.params:
        d = space.params.directory
        if isinstance(d, bytes):
            d = d.decode("utf-8", "replace")
        if d:
            return d
    return bpy.context.window_manager.svb_current_dir


def rebuild_scenes(wm, dirpath: str):
    """Scan disk and populate wm.svb_scenes collection."""
    if not dirpath:
        wm.svb_scenes.clear()
        wm.svb_current_dir = ""
        return

    prefs = preferences.get_prefs()
    include_blend1 = prefs.include_blend1 if prefs else False
    settings = wm.svb_settings

    scene_data = scanner.scan_directory(
        dirpath,
        show_unversioned=settings.show_unversioned,
        include_blend1=include_blend1,
        sort_by=settings.sort_by,
    )

    # Preserve expansion states if in same directory
    expanded_stems = {
        s.stem for s in wm.svb_scenes if s.is_expanded
    } if dirpath == wm.svb_current_dir else set()

    wm.svb_scenes.clear()
    for g in scene_data:
        item = wm.svb_scenes.add()
        item.name = g["name"]
        item.stem = g["stem"]
        item.latest_filename = g["latest_filename"]
        item.latest_version_label = g["latest_version_label"]
        item.latest_filesize = g["latest_filesize"]
        item.latest_mtime = g["latest_mtime"]
        item.version_count = g["version_count"]
        item.is_versioned = g["is_versioned"]
        item.is_expanded = g["stem"] in expanded_stems

        for v in g["versions"]:
            v_item = item.versions.add()
            v_item.filename = v["filename"]
            v_item.version_label = v["version_label"]
            v_item.version_num = v["version_num"]
            v_item.size_str = v["size_str"]
            v_item.mtime_str = v["mtime_str"]

    wm.svb_current_dir = dirpath


class SVB_OT_open_file(bpy.types.Operator):
    bl_idname = "svb.open_file"
    bl_label = "Open Scene"
    bl_description = "Open this scene file immediately"
    bl_options = {'INTERNAL'}

    filename: StringProperty(name="Filename")

    def execute(self, context):
        if not self.filename:
            return {'CANCELLED'}

        space = active_file_space(context)
        wm = context.window_manager

        # 1. Inside an active operator file dialog (e.g. File > Open, Import, Link)
        if space is not None and space.active_operator is not None:
            space.params.filename = self.filename
            try:
                bpy.ops.file.execute()
            except RuntimeError as exc:
                self.report({'ERROR'}, f"Failed to execute file open: {exc}")
                return {'CANCELLED'}
            return {'FINISHED'}

        # 2. Inside a standalone File Browser editor
        target_dir = wm.svb_current_dir or get_current_directory(context)
        filepath = os.path.join(target_dir, self.filename)

        if not os.path.exists(filepath):
            self.report({'ERROR'}, f"File does not exist: {filepath}")
            return {'CANCELLED'}

        try:
            bpy.ops.wm.open_mainfile(filepath=filepath)
            self.report({'INFO'}, f"Opened: {self.filename}")
        except RuntimeError as exc:
            self.report({'ERROR'}, f"Could not open file: {exc}")
            return {'CANCELLED'}

        return {'FINISHED'}


class SVB_OT_refresh(bpy.types.Operator):
    bl_idname = "svb.refresh"
    bl_label = "Refresh Scenes"
    bl_description = "Rescan the active directory for .blend files and versions"

    def execute(self, context):
        dirpath = get_current_directory(context)
        rebuild_scenes(context.window_manager, dirpath)

        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'FILE_BROWSER':
                    area.tag_redraw()

        return {'FINISHED'}


class SVB_OT_toggle_expand(bpy.types.Operator):
    bl_idname = "svb.toggle_expand"
    bl_label = "Toggle Past Versions"
    bl_description = "Show or hide previous version saves for this scene"
    bl_options = {'INTERNAL'}

    scene_index: IntProperty()

    def execute(self, context):
        scenes = context.window_manager.svb_scenes
        if 0 <= self.scene_index < len(scenes):
            scenes[self.scene_index].is_expanded = not scenes[self.scene_index].is_expanded
        return {'FINISHED'}


class SVB_OT_isolate_scene(bpy.types.Operator):
    bl_idname = "svb.isolate_scene"
    bl_label = "Show in Grid"
    bl_description = "Filter the main file grid to display all versions of this scene"
    bl_options = {'INTERNAL'}

    stem: StringProperty()

    def execute(self, context):
        space = active_file_space(context)
        if space and space.params:
            space.params.filter_search = self.stem + "*"
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'FILE_BROWSER':
                        area.tag_redraw()
        return {'FINISHED'}


class SVB_OT_clear_isolation(bpy.types.Operator):
    bl_idname = "svb.clear_isolation"
    bl_label = "Show All in Grid"
    bl_description = "Clear search filter in the main file grid"

    def execute(self, context):
        space = active_file_space(context)
        if space and space.params:
            space.params.filter_search = ""
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type == 'FILE_BROWSER':
                        area.tag_redraw()
        return {'FINISHED'}


classes = (
    SVB_OT_open_file,
    SVB_OT_refresh,
    SVB_OT_toggle_expand,
    SVB_OT_isolate_scene,
    SVB_OT_clear_isolation,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
