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


# ---------------------------------------------------------------------------
# UIList Handlers
# ---------------------------------------------------------------------------
class OBJECT_UL_cutouts(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "offset")
        layout.prop(item, "dimensions")


# ---------------------------------------------------------------------------
# List Operators
# ---------------------------------------------------------------------------
class JVAddCutout(bpy.types.Operator):
    bl_idname = "object.jv_add_cutout"
    bl_label = "Add Cutout"
    bl_description = "JARCH Vis: Add Cutout"

    def execute(self, context):
        props = context.object.jv_properties
        props.cutouts.add()
        props.cutouts_index = min(len(props.cutouts)-1, props.cutouts_index+1)

        bpy.ops.object.jv_update()

        return {"FINISHED"}


class JVDeleteCutout(bpy.types.Operator):
    bl_idname = "object.jv_delete_cutout"
    bl_label = "Delete Cutout"
    bl_description = "JARCH Vis: Delete Cutout"

    def execute(self, context):
        props = context.object.jv_properties

        if 0 <= props.cutouts_index < len(props.cutouts):
            props.cutouts.remove(props.cutouts_index)
            props.cutouts_index = max(0, props.cutouts_index-1)

            bpy.ops.object.jv_update()

        return {"FINISHED"}


classes = (
    JVFlooringAdd,
    JVSidingAdd,
    JVRoofingAdd,

    JVDelete,
    JVUpdate,

    OBJECT_UL_cutouts,

    JVAddCutout,
    JVDeleteCutout
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
