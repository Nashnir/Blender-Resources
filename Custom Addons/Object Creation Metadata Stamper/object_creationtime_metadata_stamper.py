# object_creationtime_metadata_stamper.py

# =============================================================================
# Object Creation-Time Metadata Stamper Addon
# =============================================================================
#
# INSTALLATION
# ------------
# 1. Save this file as:
#
#       object_creationtime_metadata_stamper.py
#
# 2. In Blender, go to:
#
#       Edit > Preferences > Add-ons
#
# 3. Click:
#
#       Install from Disk...
#
# 4. Select this .py file.
#
# 5. Enable the addon named:
#
#       Object Creation-Time Metadata Stamper
#
#
# WHAT THIS ADDON DOES
# --------------------
# This addon automatically adds metadata to every new object created
# after the addon is enabled.
#
# This includes newly added meshes, lights, cameras, duplicated objects, and
# imported objects.
#
# Currently stamps created_at_utc and created_by
#
# WHERE THE METADATA IS STORED
# ----------------------------
# The metadata is stored directly on the Blender Object as a Custom Property.
#
# You can view it here:
#
#       Select Object > Object Properties > Custom Properties
#
# The property name is:
#
#       created_at_utc, created_by
#
# Example value:
#
#       2026-06-06T04:12:30+00:00, Nashnir
#
#
# IMPORTANT NOTES
# ---------------
# - Existing objects are not stamped when the addon is first enabled.
# - Only objects created after the addon is active receive the stamp.
# - The stamp is stored on the Object, not on the Mesh data-block.
# - Time is stored in UTC so it remains consistent across time zones.
#
# =============================================================================

bl_info = {
    "name": "Object Creation-Time Metadata Stamper",
    "author": "Nashnir",
    "version": (1, 0, 0),
    "blender": (5, 1, 2),
    "category": "Object",
}

import bpy
from bpy.app.handlers import persistent
from datetime import datetime, timezone

# KEYS
CREATED_AT_KEY = "created_at_utc"
CREATED_BY_KEY = "created_by"

# VALUES
AUTHOR = "Nashnir"

_seen_object_uids = set()
_initialized = False

def now_utc_string():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def stamp_time_on_object(obj):
    if CREATED_AT_KEY not in obj:
        obj[CREATED_AT_KEY] = now_utc_string()

def stamp_author_on_object(obj):
    if CREATED_BY_KEY not in obj:
        obj[CREATED_BY_KEY] = AUTHOR

def rebuild_seen_objects():
    """
    Mark current objects as already known.
    This prevents old objects from being stamped when the addon is enabled.
    """
    global _seen_object_uids, _initialized

    _seen_object_uids = {obj.session_uid for obj in bpy.data.objects}
    _initialized = True

    return None  # important: stops the timer from repeating

@persistent
def on_file_loaded(dummy):
    global _initialized

    _initialized = False
    bpy.app.timers.register(rebuild_seen_objects, first_interval=0.1)

@persistent
def on_depsgraph_update(scene, depsgraph):
    global _initialized

    if not _initialized:
        return

    for obj in bpy.data.objects:
        uid = obj.session_uid

        if uid in _seen_object_uids:
            continue

        _seen_object_uids.add(uid)
        stamp_time_on_object(obj)
        stamp_author_on_object(obj)

def register():
    # Do NOT access bpy.data.objects directly here.
    # Blender may still be in a restricted addon-enable state?
    # Not sure
    global _initialized
    _initialized = False

    if on_depsgraph_update not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(on_depsgraph_update)

    if on_file_loaded not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(on_file_loaded)

    if not bpy.app.timers.is_registered(rebuild_seen_objects):
        bpy.app.timers.register(rebuild_seen_objects, first_interval=0.1)

def unregister():
    global _seen_object_uids, _initialized

    if on_depsgraph_update in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(on_depsgraph_update)

    if on_file_loaded in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.remove(on_file_loaded)

    if bpy.app.timers.is_registered(rebuild_seen_objects):
        bpy.app.timers.unregister(rebuild_seen_objects)

    _seen_object_uids.clear()
    _initialized = False

if __name__ == "__main__":
    register()