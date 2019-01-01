from bpy.types import Panel
from . jv_types import get_object_type_handler


class JVPanel(Panel):
    bl_idname = "OBJECT_PT_jv_panel"
    bl_label = "JARCH Vis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    jv_add_operators = [
        ("object.jv_add_flooring", "MESH_GRID"),
        ("object.jv_add_siding", "MOD_TRIANGULATE"),
        ("object.jv_add_roofing", "LINCURVE")
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

            # cutouts
            layout.separator()
            box = layout.box()
            box.prop(props, "add_cutouts", icon="MOD_BOOLEAN")

            if props.add_cutouts:
                row = box.row()
                row.template_list("OBJECT_UL_cutouts", "", props, "cutouts", props, "cutouts_index", rows=5)

                column = row.column()
                column.operator("object.jv_add_cutout", text="", icon="ADD")
                column.operator("object.jv_delete_cutout", text="", icon="REMOVE")

            layout.separator()
            box = layout.box()
            row = box.row()
            row.prop(props, "update_automatically", icon="FILE_REFRESH")
            if not props.update_automatically:
                row.operator("object.jv_update", icon="FILE_REFRESH")

            box.separator()
            for op_name, icon in self.jv_consistent_operators:
                box.operator(op_name, icon=icon)
        else:
            pass  # convert

        layout.separator()
        box = layout.box()
        for op_name, icon in self.jv_add_operators:
            box.operator(op_name, icon=icon)


def register():
    from bpy.utils import register_class

    register_class(JVPanel)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(JVPanel)


if __name__ == "__main__":
    register()
