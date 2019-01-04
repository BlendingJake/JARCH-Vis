import bpy
import bmesh
from . jv_types import get_object_type_handler
from . jv_utils import Units, determine_face_group_scale_rot_loc, determine_bisecting_planes


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


class JVConvert(bpy.types.Operator):
    bl_idname = "object.jv_convert"
    bl_label = "Convert Object"
    bl_description = "JARCH Vis: Convert Object"

    def execute(self, context):
        props = context.object.jv_properties

        # if the scale isn't (1.0, 1.0, 1.0) - raise a fuse
        if not all([i == 1 for i in context.object.scale]) and not all([i == 0 for i in context.object.rotation_euler]):
            self.report({"ERROR"}, "The scale and rotation must be applied on this object before conversion")
            return {"FINISHED"}

        # create view layer if needed
        if "JARCH VIS" not in context.scene.view_layers:
            context.scene.view_layers.new(name="JARCH VIS")

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

                    edges = set()
                    for face in fg_mesh.faces:
                        if face.index in indices:
                            for edge in face.edges:
                                if edge.is_boundary:
                                    edges.add(edge)

                    fg.bisecting_planes.clear()  # remove any planes from a previous conversion
                    determine_bisecting_planes(edges, vertices, fg, faces[0].normal, fg.location)
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
                    fg.convert_object = new_obj
                    bm.free()

                    new_obj.hide_viewport = True

            bpy.ops.mesh.primitive_cube_add()
            context.object.location = src.location
            context.object.jv_properties.convert_source_object = src
            src.hide_viewport = True
            context.object.jv_properties.object_type = "flooring"  # will automatically call update

        return {"FINISHED"}


# ---------------------------------------------------------------------------
# UIList Handlers
# ---------------------------------------------------------------------------
class OBJECT_UL_cutouts(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "offset")
        layout.prop(item, "dimensions")


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
    JVFlooringAdd,
    JVSidingAdd,
    JVRoofingAdd,

    JVDelete,
    JVUpdate,
    JVConvert,

    OBJECT_UL_cutouts,
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
