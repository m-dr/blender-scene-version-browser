import bpy
from bpy.props import BoolProperty, EnumProperty


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

    sidebar_location: EnumProperty(
        name="Sidebar",
        description="Where the scene list is shown in the File Browser",
        items=[
            ('LEFT', "Left Sidebar",
             "Show the list in the left File Browser sidebar, under Bookmarks/Recent "
             "(always visible, also in Blender 5.3 file dialogs)"),
            ('RIGHT', "Right Sidebar",
             "Show the list in the File Browser details sidebar "
             "(Blender 5.3 hides that sidebar by default in file dialogs)"),
            ('AUTO', "Automatic",
             "Use the right sidebar when the File Browser shows it, otherwise the left one"),
        ],
        default='LEFT',
        update=_on_pref_update,
    )

    panel_state: EnumProperty(
        name="Panel",
        description="Initial open/closed state of the scene list panel",
        items=[
            ('COLLAPSED', "Collapsed",
             "Always start folded (you can still expand it inside a file dialog)"),
            ('EXPANDED', "Expanded", "Always start open"),
            ('REMEMBER', "Remember Last",
             "Reopen with the open/closed state you left it in; clicking the panel header updates it"),
        ],
        default='COLLAPSED',
        update=_on_pref_update,
    )

    panel_expanded: BoolProperty(
        name="Panel Open",
        description="Open state stored by the \"Remember Last\" panel mode (also toggled by the panel header)",
        default=False,
        update=_on_pref_update,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "sidebar_location")
        col.prop(self, "panel_state")
        if self.panel_state == 'REMEMBER':
            col.prop(self, "panel_expanded")
        col.separator()
        col.prop(self, "include_blend1")


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
