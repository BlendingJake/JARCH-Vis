# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from bpy.types import Panel
from . jv_types import get_object_type_handler


class JVPanel(Panel):
    bl_idname = "OBJECT_PT_jv_panel"
    bl_label = "JARCH Vis"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    jv_add_operators = [
        ("flooring", "Add Flooring", "MESH_GRID"),
        ("siding", "Add Siding", "MOD_TRIANGULATE"),
        ("roofing", "Add Roofing", "LINCURVE"),
        ("windows", "Add Window", "MOD_WIREFRAME")
    ]

    jv_consistent_operators = [
        ("object.jv_delete", "CANCEL"),
    ]

    def draw(self, context):
        layout = self.layout
        obj = context.object

        if obj is None or obj.type != "MESH":
            # add operators
            layout.separator()
            box = layout.box()
            for tp, label, icon in self.jv_add_operators:
                op = box.operator("object.jv_add_object", text=label, icon=icon)
                op.object_type = tp

            return

        props = obj.jv_properties
        if context.mode == "OBJECT":
            if props.object_type == "none" and props.object_type_converted == "none":  # convert
                layout.operator("object.jv_convert", icon="MOD_EXPLODE")
            elif props.object_type != "none" or props.object_type_converted != "none":
                converted = props.convert_source_object is not None

                if converted:
                    layout.prop(props, "object_type_converted", icon="MATERIAL")
                else:
                    layout.prop(props, "object_type", icon="MATERIAL")
                layout.separator()

                handler = get_object_type_handler(props.object_type_converted if converted else props.object_type)
                if handler is not None:
                    handler.draw(props, layout)

                # cutouts
                if handler.is_cutable:
                    layout.separator()
                    box = layout.box()
                    box.prop(props, "add_cutouts", icon="MOD_BOOLEAN")

                    if props.add_cutouts:
                        for i in range(len(props.cutouts)):
                            cutout = props.cutouts[i]

                            box.separator()
                            ib = box.box()

                            ib.row().prop(cutout, "location")
                            ib.row().prop(cutout, "dimensions")
                            ib.row().prop(cutout, "rotation")
                            ib.prop(cutout, "local", icon="EMPTY_ARROWS")

                            op = ib.operator("object.jv_delete_cutout", icon="REMOVE")
                            op.index = i

                        box.separator()
                        box.operator("object.jv_add_cutout", icon="ADD")

                layout.separator()
                box = layout.box()
                row = box.row()
                row.prop(props, "update_automatically", icon="FILE_REFRESH")
                if not props.update_automatically:
                    row.operator("object.jv_update", icon="FILE_REFRESH")

                box.separator()
                for op_name, icon in self.jv_consistent_operators:
                    box.operator(op_name, icon=icon)

            # add operators
            layout.separator()
            box = layout.box()
            for tp, label, icon in self.jv_add_operators:
                op = box.operator("object.jv_add_object", text=label, icon=icon)
                op.object_type = tp

        elif context.mode == "EDIT_MESH":
            if props.object_type == "none":
                row = layout.row(align=True)
                row.template_list("OBJECT_UL_face_groups", "", props, "face_groups", props, "face_groups_index", rows=5)

                column = row.column(align=True)
                column.operator("object.jv_add_face_group", text="", icon="ADD")
                column.operator("object.jv_delete_face_group", text="", icon="REMOVE")

                indices = []
                for fg in props.face_groups:
                    indices.extend([i for i in fg.face_indices.split(",")])

                layout.separator()
                layout.label(text="{}/{} Faces in Face Groups".format(len(indices), len(context.object.data.polygons)),
                             icon="INFO")


def register():
    from bpy.utils import register_class

    register_class(JVPanel)


def unregister():
    from bpy.utils import unregister_class

    unregister_class(JVPanel)


if __name__ == "__main__":
    register()
