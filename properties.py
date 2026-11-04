import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty,
)


def _on_settings_update(self, context):
    try:
        from . import operators
        operators.tag_file_browsers_redraw(context)
    except Exception as e:
        print(f"[SVB] Error in settings update callback: {e}")


class SVB_Settings(bpy.types.PropertyGroup):
    show_unversioned: BoolProperty(
        name="Single Files",
        description="Include .blend files that do not follow incremental versioning",
        default=True,
        update=_on_settings_update,
    )
    sort_by: EnumProperty(
        name="Sort By",
        items=[
            ('NAME_ASC', "Name Ascending", "Sort alphabetically by scene name (A-Z)"),
            ('NAME_DESC', "Name Descending", "Sort reverse-alphabetically by scene name (Z-A)"),
            ('DATE_DESC', "Date Modified Descending", "Sort by latest modified date (newest first)"),
            ('DATE_ASC', "Date Modified Ascending", "Sort by latest modified date (oldest first)"),
        ],
        default='NAME_ASC',
        update=_on_settings_update,
    )
    search_query: StringProperty(
        name="Filter",
        description="Filter scenes by name",
        default="",
    )


classes = (
    SVB_Settings,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.WindowManager.svb_settings = PointerProperty(type=SVB_Settings)


def unregister():
    del bpy.types.WindowManager.svb_settings

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
