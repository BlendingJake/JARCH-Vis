# This file is part of JARCH Vis
#
# JARCH Vis is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# JARCH Vis is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with JARCH Vis.  If not, see <http://www.gnu.org/licenses/>.

# constants
METRIC_INCH = 39.3701
METRIC_FOOT = 3.28084
I = 1 / METRIC_INCH
HI = 0.5 / METRIC_INCH


def delete_materials(self, context):
    import bpy
    o = context.object
    if not o.jv_is_material:
        for i in o.data.materials:
            bpy.ops.object.material_slot_remove()

        for i in bpy.data.materials:
            if i.users == 0:
                bpy.data.materials.remove(i)


def preview_materials(self, context):
    import bpy
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    if bpy.context.object.jv_is_preview:
                        space.viewport_shade = 'RENDERED'
                    else:
                        space.viewport_shade = "SOLID"


def unwrap_object(self, context):
    import bpy

    o = context.object
    for ob in context.selected_objects:
        ob.select = False
    o.select = True
    context.scene.objects.active = o

    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.cube_project()
    bpy.ops.object.editmode_toggle()


def random_uvs(self, context):
    import bpy
    import bmesh
    from mathutils import Vector
    from random import uniform
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action="SELECT")
    obj = bpy.context.object
    me = obj.data
    bm = bmesh.from_edit_mesh(me)

    uv_layer = bm.loops.layers.uv.verify()
    bm.faces.layers.tex.verify()
    # adjust UVs
    for f in bm.faces:
        offset = Vector((uniform(-1.0, 1.0), uniform(-1.0, 1.0)))
        for v in f.loops:
            luv = v[uv_layer]
            luv.uv = (luv.uv + offset).xy

    bmesh.update_edit_mesh(me)
    bpy.ops.object.editmode_toggle()


def update_roofing_facegroup_selection(self, context):
    import bpy
    # updates which faces are selected based on which face group is selected in the UI##
    ob = context.object
    bpy.ops.object.editmode_toggle()

    if len(ob.jv_face_groups) >= 1:
        fg = ob.jv_face_groups[ob.jv_face_group_index]

        # deselect all faces and edges
        for f in ob.data.polygons:
            f.select = False
        for e in ob.data.edges:
            e.select = False

            # get info from face group and use to define selection
        st = fg.data.split(",")
        del st[len(st) - 1]

        temp_l = []
        for i in st:
            st2 = i.split("+")
            tl = (float(st2[0]), float(st2[1]), float(st2[2]))
            temp_l.append(tl)

            # select correct faces
        for f in temp_l:
            for face_in_obj in ob.data.polygons:
                if round_tuple(tuple(face_in_obj.center), 4) == f:
                    face_in_obj.select = True

        # make sure selection list is up to date
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

    bpy.ops.object.editmode_toggle()


# convert
def convert(num, to):
    if to == "ft":
        out = num / 3.28084
    else:
        out = num / 39.3701
    re = round(out, 5)
    return re


# point rotation
def point_rotation(data, origin, rot):
    from math import sin, cos
    # Takes in a single tuple (x, y) or a tuple of tuples ((x, y), (x, y)) and rotates them rot or [rot1, rot2] radians
    # around origin where rot1, rot2 match up to tuples in data so each point can have a separate rotation,
    # returns new (x, y) or ((x, y), (x, y)) values###
    data_list = []
    if isinstance(data[0], float) or isinstance(data[0], int):
        data_list.append(data)
    else:
        data_list = data

    if isinstance(rot, float) or isinstance(rot, int):
        rot_list = [rot] * len(data_list)
    else:
        rot_list = rot

    out_list = []
    ct = 0
    for point in data_list:
        new_point = (point[0] - origin[0], point[1] - origin[1])
        x = new_point[0]
        y = new_point[1]
        cur_rot = rot_list[ct]
        new_x = (x * cos(cur_rot)) - (y * sin(cur_rot))
        new_y = (x * sin(cur_rot)) - (y * cos(cur_rot))
        out = (new_x + origin[0], new_y + origin[1])
        out_list.append((out[0], out[1]))
        ct += 1

    if isinstance(data[0], float) or isinstance(data[0], int):
        return out_list[0]
    else:
        return out_list


# find objects rotation
def object_rotation(obj):
    from math import atan, radians    
    # get list of vertices
    verts = [(obj.matrix_world * i.co).to_tuple() for i in obj.data.vertices]
    # create temporary list then round any numbers that are really small to zero
    v1_temp = verts[0]
    v1 = []
    for num in v1_temp:
        if -0.00001 < num < 0.00001:
            num = 0.0
        v1.append(round(num, 5))
    # find numbers that work with the original number
    v2_temp = 0
    for i in verts:
        i2 = []
        for num in i:  # round off numbers if close
            if -0.00001 < num < 0.00001:
                num = 0.0
            i2.append(round(num, 5))
        # are number correct?
        if (i2[0] != v1[0] and i2[1] == v1[1]) or (i2[0] == v1[0] and i2[1] != v1[1]) or (i2[0] != v1[0] and i2[1] != v1[1]) and v2_temp == 0:
            v2_temp = i2
    # calculate angle
    if v2_temp != 0:
        skip = True if v2_temp[0] != v1[0] and v2_temp[1] == v1[1] else False  # plane is inline with x-axis

        if not skip:
            v2 = (v2_temp[0] - v1[0], v2_temp[1] - v1[1], v2_temp[2] - v1[2])
            if v2[0] != 0:
                angle = atan(v2[1] / v2[0])
            else:
                angle = radians(90)
        else:
            angle = 0
    else:
        angle = radians(90)

    return angle


# TODO: fix to account for rotation on x-axis
# figure exact object dimensions
def object_dimensions(obj):
    from math import sqrt
    
    verts = [(obj.matrix_world * i.co).to_tuple() for i in obj.data.vertices]
    sx, bx, sy, by, sz, bz = 0, 0, 0, 0, 0, 0

    for val in verts:
        # x axis
        if val[0] < sx:
            sx = val[0]
        elif val[0] > bx:
            bx = val[0]
        # y axis
        if val[1] < sy:
            sy = val[1]
        elif val[1] > by:
            by = val[1]
        # z axis
        if val[2] < sz:
            sz = val[2]
        elif val[2] > bz:
            bz = val[2]
    # lengths
    x = (round(bx - sx, 5)) * obj.scale[0]
    y = (round(by - sy, 5)) * obj.scale[1]
    z = (round(bz - sz, 5)) * obj.scale[2]

    dia = sqrt(x ** 2 + y ** 2)
    
    return [dia, z]


def round_tuple(tup, digits):
    temp = []
    for i in tup:
        temp.append(round(i, digits))
    return tuple(temp)


def rot_from_normal(normal):
    from math import radians, atan, acos
    theta = radians(90)
    if normal[0]:
        theta = abs(atan(normal[1] / normal[0]))

    if normal[0] <= 0:
        if normal[1] > 0:
            theta = radians(180) - theta
        else:
            theta += radians(180)
    elif normal[1] < 0:
        theta *= -1

    phi = acos(normal[2])

    return 0, phi, theta


# adds all values from v into l
def append_all(original_list: list, values: list):
    for i in values:
        original_list.append(i)


def apply_modifier_boolean(bpy, ob, bool_name: str):
    bpy.ops.object.modifier_add(type="BOOLEAN")
    pos = len(ob.modifiers) - 1
    bpy.context.object.modifiers[pos].object = bpy.data.objects[bool_name]
    bpy.context.object.modifiers[pos].solver = "CARVE"
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier=ob.modifiers[0].name)


def round_rad(deg: float, r=4) -> float:
    from math import radians
    return round(radians(deg), r)
