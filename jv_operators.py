import bpy
from . jv_types import get_object_type_handler


# ---------------------------------------------------------------------------
# Architecture Specific Operators
# ---------------------------------------------------------------------------
class JVFlooringAdd(bpy.types.Operator):
    bl_idname = "object.jv_add_flooring"
    bl_label = "Add Flooring"
    bl_description = "JARCH Vis: Add Flooring"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object

        o.jv_properties.object_type = "flooring"

        return {"FINISHED"}


class JVSidingAdd(bpy.types.Operator):
    bl_idname = "object.jv_add_siding"
    bl_label = "Add Siding"
    bl_description = "JARCH Vis: Add Siding"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object

        o.jv_properties.object_type = "siding"

        return {"FINISHED"}


class JVRoofingAdd(bpy.types.Operator):
    bl_idname = "object.jv_add_roofing"
    bl_label = "Add Roofing"
    bl_description = "JARCH Vis: Add Roofing"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object

        o.jv_properties.object_type = "roofing"

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# Generic Operators
# ---------------------------------------------------------------------------
class JVDelete(bpy.types.Operator):
    bl_idname = "object.jv_delete"
    bl_label = "Delete Object"
    bl_description = "JARCH Vis: Delete Object"

    def execute(self, context):
        handler = get_object_type_handler(context.object.jv_properties.object_type)

        if handler is not None:
            handler.delete(context.object.jv_properties, context)

        return {"FINISHED"}


class JVUpdate(bpy.types.Operator):
    bl_idname = "object.jv_update"
    bl_label = "Update Object"
    bl_description = "JARCH Vis: Update Object"

    def execute(self, context):
        handler = get_object_type_handler(context.object.jv_properties.object_type)

        if handler is not None:
            handler.update(context.object.jv_properties, context)

        return {"FINISHED"}


classes = (
    JVFlooringAdd,
    JVSidingAdd,
    JVRoofingAdd,

    JVDelete,
    JVUpdate
)


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class

    for cls in classes:
        unregister_class(cls)


if __name__ == "__main__":
    register()
