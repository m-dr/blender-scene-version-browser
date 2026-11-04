import bpy
from bpy.props import BoolProperty


def _on_pref_update(self, context):
    try:
        from . import scanner, operators
        scanner.invalidate_cache()
        operators.tag_file_browsers_redraw(context)
    except Exception:
        pass


class SVB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or "scene_version_browser"

    include_blend1: BoolProperty(
        name="Include .blend1 Backups",
        description="Include .blend1 and older backup files in the version history",
        default=False,
        update=_on_pref_update,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "include_blend1")


def get_prefs() -> SVB_AddonPreferences:
    addon = bpy.context.preferences.addons.get(__package__ or "scene_version_browser")
    return addon.preferences if addon else None


classes = (
    SVB_AddonPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
