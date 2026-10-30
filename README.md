# Scene Version Browser (DEV)

Filter scene sequence saves and display only the latest version of incremental `.blend` files directly in Blender's File Browser.

---

## Overview

When working on complex projects with frequent incremental saves (`_v001`, `_v002`, `_v015`), navigating a directory with dozens of `.blend` files becomes tedious. 

**Scene Version Browser** adds a companion sidebar panel to the File Browser that:
- Intelligently groups incremental `.blend` saves by base scene name.
- Displays only the **latest version** by default (`Scene_Shot01 [v014]`).
- Opens the latest version with **1 single click** directly through Blender's native open operator.
- Features an expandable history dropdown to inspect or open previous versions (`v013`, `v012`) for quick rollbacks.
- Includes an **Isolate in Grid** button to synchronize Blender's native file grid to show all versions of a specific scene family.

---

## Where the Panel Appears

1. **In Operator Dialogs (`File > Open`, `File > Link`, `File > Append`)**:
   - Appears in the **right-hand options sidebar** under the operator settings.
   - Automatically slides open so you don't need to manually press `N`.
2. **In Standalone File Browser Editors**:
   - Appears via a **`Scenes`** popover button directly in the File Browser header next to the native filter controls.

---

## Supported Version Conventions

The version detection engine recognizes common studio and solo conventions:
- `Shot01_Lighting_v001.blend`, `Shot01_Lighting_v002.blend`
- `Character_Rig_V1.blend`, `Character_Rig_V2.blend`
- `Environment.001.blend`, `Environment.002.blend`
- `Vehicle_Model-v05.blend`
- Standalone unversioned `.blend` files (can be toggled on/off via the **Singles** filter).

---

## Building the Package

To build the sanitized release archive:
```powershell
python scripts/build_extension.py
```
This generates `dist/scene_version_browser-0.1.0.zip` ready for catalog publishing.
