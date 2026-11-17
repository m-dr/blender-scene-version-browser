bl_info = {
    "name": "Scene Version Browser (DEV)",
    "author": "MD <m-dr>",
    "version": (0, 1, 4),
    "blender": (5, 2, 0),
    "location": "File Browser > Sidebar & Header",
    "description": "Filter scene sequences and display only the latest version of incremental saves in the File Browser",
    "category": "Pipeline",
}

import importlib
from . import preferences, properties, scanner, operators, ui

modules = (preferences, properties, scanner, operators, ui)


def register():
    for mod in modules:
        try:
            importlib.reload(mod)
        except Exception:
            pass

    for mod in modules:
        if hasattr(mod, "register"):
            mod.register()


def unregister():
    for mod in reversed(modules):
        if hasattr(mod, "unregister"):
            try:
                mod.unregister()
            except Exception:
                pass


if __name__ == "__main__":
    register()
