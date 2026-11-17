import bpy
from bpy.props import BoolProperty, EnumProperty


def _on_pref_update(self, context):
    try:
        from . import scanner, operators
        scanner.invalidate_cache()
        operators.tag_file_browsers_redraw(context)
    except Exception:
        pass


def _on_panel_state_update(self, context):
    # The panel always reads panel_expanded; the mode only sets its default.
    if self.panel_state == 'COLLAPSED':
        self.panel_expanded = False
    elif self.panel_state == 'EXPANDED':
        self.panel_expanded = True
    _on_pref_update(self, context)


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
            ('COLLAPSED', "Collapsed", "Start folded (default for a new session)"),
            ('EXPANDED', "Expanded", "Start open"),
            ('REMEMBER', "Remember Last",
             "Keep whatever open/closed state you left the panel in"),
        ],
        default='COLLAPSED',
        update=_on_panel_state_update,
    )

    panel_expanded: BoolProperty(
        name="Panel Open",
        description="Current open state of the scene list panel (also toggled by the panel header)",
        default=False,
        update=_on_pref_update,
    )

    name_clickable: BoolProperty(
        name="Clickable Name Row",
        description="Make the whole scene-name line a button that opens the latest version. "
                    "Turn off to draw the name flush against the card edge (not clickable)",
        default=True,
        update=_on_pref_update,
    )

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "sidebar_location")
        col.prop(self, "panel_state")
        col.prop(self, "panel_expanded")
        col.separator()
        col.prop(self, "name_clickable")
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
