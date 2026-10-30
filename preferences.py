import bpy
from bpy.props import BoolProperty, FloatProperty


class SVB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__ or "scene_version_browser"

    auto_open_options: BoolProperty(
        name="Auto-Open Sidebar in File Dialogs",
        description="Automatically open the right-hand options sidebar in File > Open and import dialogs",
        default=True,
    )

    include_blend1: BoolProperty(
        name="Include .blend1 Backups",
        description="Include .blend1 and older backup files in the version history",
        default=False,
    )

    poll_interval: FloatProperty(
        name="Poll Interval (seconds)",
        description="How often to check for directory navigation in the File Browser",
        default=0.5,
        min=0.1,
        max=5.0,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "auto_open_options")
        layout.prop(self, "include_blend1")
        layout.prop(self, "poll_interval")


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
