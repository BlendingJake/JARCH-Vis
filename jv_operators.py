import bpy
from jv_flooring import JVFlooring


class JVFlooringAdd(bpy.types.Operator):
    bl_idname = "object.jv_flooring_add"
    bl_label = "Add Flooring"
    bl_description = "JARCH Vis: Add Flooring"

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.objects.active
        o.jv_builder = JVFlooring(o)

        return {"FINISHED"}


class JVDelete(bpy.types.Operator):
    bl_idname = "object.jv_delete"
    bl_label = "Delete Object"
    bl_description = "JARCH Vis: Delete Object"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.jv_builder is not None

    def execute(self, _):
        bpy.ops.object.delete()


class JVUpdate(bpy.types.Operator):
    bl_idname = "object.jv_update"
    bl_label = "Update Object"
    bl_description = "JARCH Vis: Update Object"

    @classmethod
    def poll(cls, context):
        return context.object and context.object.jv_builder is not None

    def execute(self, context):
        context.object.jv_builder.update()
