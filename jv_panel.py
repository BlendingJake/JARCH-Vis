from bpy.types import Panel


class JVPanel(Panel):
    bl_idname = "OBJECT_PT_jv_panel"
    bl_label = "JARCH Vis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "JARCH Vis"

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

        if obj.get("jv_builder", None) is not None:
            obj.jv_builder.draw(layout)

            layout.separator()
            for op_name, icon in self.jv_consistent_operators:
                layout.operator(op_name, icon=icon)
        else:
            pass  # convert

        layout.separator()
        for op_name, icon in self.jv_add_operators:
            layout.operator(op_name, icon=icon)
