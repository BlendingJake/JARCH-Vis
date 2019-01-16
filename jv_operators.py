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

import bpy
import bmesh
from bpy.props import IntProperty, StringProperty
from . jv_types import get_object_type_handler
from . jv_utils import Units, determine_face_group_scale_rot_loc, determine_bisecting_planes


# ---------------------------------------------------------------------------
# Generic Operators
# ---------------------------------------------------------------------------
class JVAddObject(bpy.types.Operator):
    bl_idname = "object.jv_add_object"
    bl_label = "Add JARCH Vis Object"
    bl_description = "Add JARCH Vis Object"

    object_type: StringProperty()

    def execute(self, context):
        bpy.ops.mesh.primitive_cube_add()
        o = context.object

        o.jv_properties.object_type = self.object_type

        return {"FINISHED"}


class JVDelete(bpy.types.Operator):
    bl_idname = "object.jv_delete"
    bl_label = "Delete Object"
    bl_description = "JARCH Vis: Delete Object"

    def execute(self, context):
        props = context.object.jv_properties
        converted = props.convert_source_object is not None

        handler = get_object_type_handler(props.object_type_converted if converted else props.object_type)

        if handler is not None:
            handler.delete(context.object.jv_properties, context)

        return {"FINISHED"}


class JVUpdate(bpy.types.Operator):
    bl_idname = "object.jv_update"
    bl_label = "Update Object"
    bl_description = "JARCH Vis: Update Object"

    def execute(self, context):
        props = context.object.jv_properties
        converted = props.convert_source_object is not None

        handler = get_object_type_handler(props.object_type_converted if converted else props.object_type)

        if handler is not None:
            handler.update(context.object.jv_properties, context)

        return {"FINISHED"}


class JVConvert(bpy.types.Operator):
    bl_idname = "object.jv_convert"
    bl_label = "Convert Object"
    bl_description = "JARCH Vis: Convert Object"

    def execute(self, context):
        props = context.object.jv_properties

        # if the scale isn't (1.0, 1.0, 1.0) - raise a fuse
        if not all([i == 1 for i in context.object.scale]) or not all([i == 0 for i in context.object.rotation_euler]):
            self.report({"ERROR"}, "The scale and rotation must be applied on this object before conversion")
            return {"FINISHED"}

        if len(props.face_groups) == 0:  # no face groups, so try and create one
            self.report({"ERROR"}, """Please enter edit mode and create a face group before trying to convert""")

        # divide the faces up into distinct objects that can be used for the boolean process
        # point each face group to the corresponding object
        # create a new object that will contain the architecture and update it
        else:
            src = context.object
            for fg in props.face_groups:
                indices = set([int(i) for i in fg.face_indices.split(",") if i])

                # collect needed vertices
                faces = []
                vertices = set()
                for face in src.data.polygons:
                    if face.index in indices:
                        faces.append(face)
                        for vi in face.vertices:
                            vertices.add(src.data.vertices[vi])

                # determine loc, rot, dims
                determine_face_group_scale_rot_loc(faces, list(vertices), fg)

                if fg.is_convex:
                    # if the face group is convex, then we can used bmesh.ops.bisect_plane to cut it
                    # so we have to figure out what planes need to be used to cut it based on the boundary edges
                    fg_mesh = bmesh.new()
                    fg_mesh.from_mesh(src.data)

                    all_edges = {}
                    for face in fg_mesh.faces:
                        if face.index in indices:
                            for edge in face.edges:
                                # keep track of how many faces the edge is attached to
                                if edge in all_edges:
                                    all_edges[edge] += 1
                                else:
                                    all_edges[edge] = 1

                    edges = set()
                    for edge, count in all_edges.items():
                        if count == 1:
                            edges.add(edge)

                    fg.bisecting_planes.clear()  # remove any planes from a previous conversion
                    determine_bisecting_planes(edges, vertices, fg, faces[0].normal)
                    fg_mesh.free()
                else:
                    # if the face group isn't convex, then we have to create a boolean object to use as a cutter
                    bm = bmesh.new()

                    # create vertices
                    new_vertex_mappings = {}  # current vertex index -> bmesh vertex
                    for vertex in vertices:
                        vert = bm.verts.new(vertex.co)
                        new_vertex_mappings[vertex.index] = vert

                    # create faces
                    for face in faces:
                        bm.faces.new([new_vertex_mappings[i] for i in face.vertices])

                    bm.normal_update()
                    bm.verts.ensure_lookup_table()
                    bm.faces.ensure_lookup_table()

                    # create new object based on this mesh data
                    bpy.ops.mesh.primitive_cube_add()
                    new_obj = context.object
                    new_obj.name = "{}.fg".format(src.name)

                    # set rotation, translation
                    new_obj.rotation_euler = src.rotation_euler
                    new_obj.location = src.location

                    # add solidify modifier
                    bpy.ops.object.modifier_add(type="SOLIDIFY")
                    new_obj.modifiers["Solidify"].thickness = 6*Units.INCH
                    new_obj.modifiers["Solidify"].offset = 0
                    new_obj.location = src.location

                    bm.to_mesh(new_obj.data)
                    fg.boolean_object = new_obj
                    bm.free()

                    new_obj.hide_viewport = True

            bpy.ops.mesh.primitive_cube_add()
            context.object.location = src.location
            context.object.jv_properties.convert_source_object = src
            src.hide_viewport = True
            context.object.jv_properties.object_type_converted = "roofing"  # will cause an automatic update

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# UIList Handlers
# ---------------------------------------------------------------------------
class OBJECT_UL_face_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text="{} face(s)".format(len(item.face_indices.split(","))))
        layout.prop(item, "is_convex", icon="MOD_SIMPLIFY")


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
        bpy.ops.object.jv_update()

        return {"FINISHED"}


class JVDeleteCutout(bpy.types.Operator):
    bl_idname = "object.jv_delete_cutout"
    bl_label = "Delete Cutout"
    bl_description = "JARCH Vis: Delete Cutout"

    index: IntProperty(name="Cutout Index")

    def execute(self, context):
        props = context.object.jv_properties

        if 0 <= self.index < len(props.cutouts):
            props.cutouts.remove(self.index)
            bpy.ops.object.jv_update()

        return {"FINISHED"}


class JVAddFaceGroup(bpy.types.Operator):
    bl_idname = "object.jv_add_face_group"
    bl_label = "Add Face Group"
    bl_description = "JARCH Vis: Add Face Group"

    def execute(self, context):
        props = context.object.jv_properties
        fg = props.face_groups.add()

        # make sure face selection gets updated
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        indices = [str(face.index) for face in context.object.data.polygons if face.select]

        if not indices:
            self.report({"ERROR"}, "At least one face must be selected to add a face group")
        else:
            fg.face_indices = ",".join(indices)
            props.face_groups_index = min(len(props.face_groups) - 1, props.face_groups_index + 1)

        return {"FINISHED"}


class JVDeleteFaceGroup(bpy.types.Operator):
    bl_idname = "object.jv_delete_face_group"
    bl_label = "Delete Face Group"
    bl_description = "JARCH Vis: Delete Face Group"

    def execute(self, context):
        props = context.object.jv_properties

        if 0 <= props.face_groups_index < len(props.face_groups):
            props.face_groups.remove(props.face_groups_index)
            props.face_groups_index = max(0, props.face_groups_index-1)

        return {"FINISHED"}


classes = (
    JVAddObject,
    JVDelete,
    JVUpdate,
    JVConvert,

    OBJECT_UL_face_groups,

    JVAddCutout,
    JVDeleteCutout,
    JVAddFaceGroup,
    JVDeleteFaceGroup
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
