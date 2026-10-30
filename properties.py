import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)


def _on_settings_update(self, context):
    try:
        from . import operators
        wm = getattr(context, "window_manager", None)
        if not wm:
            wm = bpy.context.window_manager
        dirpath = operators.get_current_directory(context)
        if dirpath:
            operators.rebuild_scenes(wm, dirpath)
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == 'FILE_BROWSER':
                        area.tag_redraw()
    except Exception as e:
        print(f"[SVB] Error in settings update callback: {e}")


class SVB_VersionItem(bpy.types.PropertyGroup):
    filename: StringProperty(name="Filename")
    version_label: StringProperty(name="Version")
    version_num: IntProperty(name="Version Number")
    size_str: StringProperty(name="Size")
    mtime_str: StringProperty(name="Modified")


class SVB_SceneGroup(bpy.types.PropertyGroup):
    name: StringProperty(name="Scene Name")
    stem: StringProperty(name="Stem")
    latest_filename: StringProperty(name="Latest Filename")
    latest_version_label: StringProperty(name="Latest Version")
    latest_filesize: StringProperty(name="Latest Size")
    latest_mtime: StringProperty(name="Latest Modified")
    version_count: IntProperty(name="Version Count", default=1)
    is_versioned: BoolProperty(name="Is Versioned", default=False)
    is_expanded: BoolProperty(name="Show Past Versions", default=False)
    versions: CollectionProperty(type=SVB_VersionItem)


class SVB_Settings(bpy.types.PropertyGroup):
    show_unversioned: BoolProperty(
        name="Single Files",
        description="Include .blend files that do not follow incremental versioning",
        default=True,
        update=_on_settings_update,
    )
    auto_refresh: BoolProperty(
        name="Auto Refresh",
        description="Automatically rescan when navigating to another directory",
        default=True,
    )
    sort_by: EnumProperty(
        name="Sort By",
        items=[
            ('DATE', "Date Modified", "Sort by latest modified date (newest first)"),
            ('NAME', "Name", "Sort alphabetically by scene name"),
        ],
        default='DATE',
        update=_on_settings_update,
    )
    search_query: StringProperty(
        name="Filter",
        description="Filter scenes by name",
        default="",
    )


classes = (
    SVB_VersionItem,
    SVB_SceneGroup,
    SVB_Settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.svb_scenes = CollectionProperty(type=SVB_SceneGroup)
    bpy.types.WindowManager.svb_active_index = IntProperty(default=-1)
    bpy.types.WindowManager.svb_current_dir = StringProperty(default="")
    bpy.types.WindowManager.svb_settings = PointerProperty(type=SVB_Settings)


def unregister():
    del bpy.types.WindowManager.svb_settings
    del bpy.types.WindowManager.svb_current_dir
    del bpy.types.WindowManager.svb_active_index
    del bpy.types.WindowManager.svb_scenes

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
