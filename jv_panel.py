from bpy.types import Panel
from . jv_types import get_object_type_handler


class JVPanel(Panel):
    bl_idname = "OBJECT_PT_jv_panel"
    bl_label = "JARCH Vis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    jv_add_operators = [
        ("object.jv_add_flooring", "MESH_GRID")
    ]

    jv_consistent_operators = [
        ("object.jv_delete", "CANCEL"),
    ]

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is not None and obj.type == "MESH":
            props = obj.jv_properties
            layout.prop(props, "object_type", icon="MATERIAL")
            layout.separator()

            handler = get_object_type_handler(props.object_type)
            if handler is not None:
                handler.draw(props, layout)

            layout.separator()
            layout.prop(props, "update_automatically", icon="FILE_REFRESH")
            if not props.update_automatically:
                layout.operator("object.jv_update", icon="FILE_REFRESH")

            layout.separator()
            for op_name, icon in self.jv_consistent_operators:
                layout.operator(op_name, icon=icon)
        else:
            pass  # convert

        layout.separator()
        for op_name, icon in self.jv_add_operators:
            layout.operator(op_name, icon=icon)


def register():
    from bpy.utils import register_class

    register_class(JVPanel)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(JVPanel)


if __name__ == "__main__":
    register()
