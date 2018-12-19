from bpy.types import Panel


class JVPanel(Panel):
    bl_idname = "OBJECT_PT_jv_panel"
    bl_label = "JARCH Vis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    jv_add_operators = [
        ("object.jv_add_flooring", "MESH_GRID")
    ]

    jv_consistent_operators = [
        ("object.jv_update", "FILE_REFRESH"),
        ("object.jv_delete", "CANCEL"),
    ]

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is not None and obj.hasattr("jv_properties") and obj.jv_properties.object_type != "":
            obj.jv_base.draw(layout)

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
