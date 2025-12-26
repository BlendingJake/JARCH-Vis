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
from math import sqrt, radians, acos, asin, sin, cos, tan
from mathutils import Vector, Euler
from . jv_builder_base import JVBuilderBase
from . jv_utils import Units
from typing import Tuple, List


class JVWindows(JVBuilderBase):
    is_cutable = False
    is_convertible = False

    @staticmethod
    def draw(props, layout):
        layout.prop(props, "window_pattern", icon="MOD_WIREFRAME")

        if props.window_pattern in ("regular", "arch", "gothic"):
            layout.separator()
            row = layout.row()
            row.prop(props, "window_width_medium")
            row.prop(props, "window_height_medium")
        elif props.window_pattern in ("polygon", "circular"):
            layout.separator()
            layout.prop(props, "window_radius")
        elif props.window_pattern == "ellipse":
            layout.separator()
            row = layout.row()
            row.prop(props, "window_width_wide")
            row.prop(props, "window_height_short")
        elif props.window_pattern in ("bow", "bay"):
            layout.separator()
            row = layout.row()
            row.prop(props, "window_width_wide")
            row.prop(props, "window_height_medium")

        layout.separator()
        layout.prop(props, "jamb_width")
        row = layout.row()
        row.prop(props, "frame_width")
        row.prop(props, "frame_thickness")

        if props.window_pattern in ("regular", "arch"):
            layout.separator()
            layout.prop(props, "slider", icon="DECORATE_OVERRIDE")

            if props.slider and props.window_pattern == "regular":
                layout.prop(props, "orientation", icon="ORIENTATION_VIEW")

        if props.window_pattern == "polygon":
            layout.separator()
            layout.prop(props, "window_side_count")

        if props.window_pattern == "circular":
            layout.separator()
            row = layout.row()
            row.prop(props, "full_circle", icon="MESH_CIRCLE")

            if not props.full_circle:
                row.prop(props, "window_angle")

        if props.window_pattern == "bay":
            layout.separator()
            row = layout.row()
            row.prop(props, "bay_angle")
            row.prop(props, "window_depth")

        if props.window_pattern == "bow":
            layout.separator()
            layout.prop(props, "bow_segments")

        if props.window_pattern == "arch":
            layout.separator()
            layout.prop(props, "window_roundness")

        if props.window_pattern in ("arch", "gothic", "ellipse", "circular"):
            layout.separator()
            layout.prop(props, "window_resolution")

        if props.window_pattern == "regular":
            layout.separator()
            layout.prop(props, "num_joined_windows")

    @staticmethod
    def update(props, context):
        mesh = JVWindows._start(context)

        getattr(JVWindows, "_{}".format(props.window_pattern))(props, mesh)

        JVWindows._finish(context, mesh)
        JVWindows._uv_unwrap(by_seams=False)

    @staticmethod
    def _update_mesh_from_geometry_lists(mesh, geometry_lists: List[Tuple[list, list, list]]):
        """
        Take all the generated geometry data and combine it into one mesh, offset face vertex index's where needed
        :param mesh: the bmesh mesh
        :param geometry_lists: a list of tuples of verts, faces, glass_ids
        :return:
        """
        vert_offset = 0
        face_offset = 0
        for verts, faces, glass_ids in geometry_lists:
            for v in verts:
                mesh.verts.new(v)
            mesh.verts.ensure_lookup_table()

            for face in faces:
                mesh.faces.new([mesh.verts[i+vert_offset] for i in face])
            mesh.faces.ensure_lookup_table()

            for fid in glass_ids:
                mesh.faces[fid+face_offset].material_index = 1

            vert_offset = len(mesh.verts)
            face_offset = len(mesh.faces)

    @staticmethod
    def _regular(props, mesh):
        width, height, jamb_w = props.window_width_medium, props.window_height_medium, props.jamb_width
        frame_width, pane_th, jamb_th = props.frame_width, props.frame_thickness, Units.INCH

        if props.orientation == "vertical":
            pane_width = width
            if props.slider:
                pane_height = (height + frame_width) / 2
            else:
                pane_height = height
        else:
            pane_height = height
            if props.slider:
                pane_width = (width + frame_width) / 2
            else:
                pane_width = width

        geometry_data = []
        x = 0
        for _ in range(props.num_joined_windows):
            tx = x
            # create jamb - keep left if first jamb
            geometry_data.append(JVWindows._rectangular_jamb_geometry(width, height, (x, 0, 0), jamb_w,
                                                                      keep_left=x == 0, th=jamb_th))

            # create first pane
            y, z, = 0, jamb_th
            if props.slider:  # first pane is offset on y if there is going to be a second pane
                y = -pane_th / 2

            geometry_data.append(JVWindows._rectangular_pane_geometry(pane_width, pane_height, (x+jamb_th, y, z),
                                                                      frame_th=pane_th, fw=frame_width))

            # # create second pane if needed
            if props.slider:
                y += pane_th
                if props.orientation == "vertical":
                    z += pane_height - frame_width
                else:
                    x += pane_width - frame_width

                geometry_data.append(JVWindows._rectangular_pane_geometry(pane_width, pane_height, (x+jamb_th, y, z),
                                                                          frame_th=pane_th, fw=frame_width))

            x = tx + width + jamb_th

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _arch(props, mesh):
        geometry_data = []
        verts, faces, glass_ids = [], [], []

        # main values
        width, height, jamb_w = props.window_width_medium, props.window_height_medium, props.jamb_width
        res, roundness = props.window_resolution, props.window_roundness / 100
        a, b, = width / 2, (width * roundness) / 2  # a, b for main window, need modified for jamb, inset frame, etc.
        frame_width, jamb_th, frame_th, inset = props.frame_width, Units.INCH, props.frame_thickness, Units.Q_INCH

        # useful to save calculations later
        hjamb_w, hframe_width, hframe_th = jamb_w / 2, frame_width / 2, frame_th / 2
        center_x, center_z = jamb_th + (width / 2), jamb_th + height - b
        vpl = res + 4  # vertices per loop

        # JAMB ----------------------------------------------------------------------
        steps = [  # start x, end x, y, z, amount to add to a and b
            (jamb_th, jamb_th+width, -hjamb_w, jamb_th, 0),  # inner on -Y
            (0, (2*jamb_th) + width, -hjamb_w, 0, jamb_th),  # outer on -Y
            (0, (2 * jamb_th) + width, hjamb_w, 0, jamb_th),  # outer on Y
            (jamb_th, jamb_th + width, hjamb_w, jamb_th, 0)  # inner on Y
        ]

        for sx, ex, y, sz, dab in steps:
            verts += [(sx, y, sz), (ex, y, sz)]
            for x, z in JVWindows._ellipse_iterator(a+dab, b+dab, res):
                verts.append((center_x+x, y, center_z+z))

        # jamb faces
        JVWindows._loop_face_builder(len(steps), vpl, faces)
        geometry_data.append((verts, faces, glass_ids))

        # PANE(S) ----------------------------------------------------------------------------------
        verts, faces, glass_ids = [], [], []  # clear for next round
        sy, sz = 0, jamb_th  # start y and z
        if props.slider:
            pane_height = center_z / 2 + frame_width
            geometry_data.append(JVWindows._rectangular_pane_geometry(width, pane_height,
                                                                      (jamb_th, -hframe_th, jamb_th),
                                                                      fw=frame_width, inset=inset,
                                                                      frame_th=frame_th))

            sy, sz = frame_th / 2, jamb_th + pane_height - frame_width

        # main pane
        steps = [  # start x, end x, y, z, amount to add to a and b
            (jamb_th+frame_width, jamb_th+width-frame_width, sy-hframe_th+inset, sz+frame_width, -frame_width),
            (jamb_th+frame_width, jamb_th+width-frame_width, sy-hframe_th, sz+frame_width, -frame_width),
            (jamb_th, jamb_th+width, sy-hframe_th, sz, 0),

            (jamb_th, jamb_th+width, sy+hframe_th, sz, 0),
            (jamb_th+frame_width, jamb_th+width-frame_width, sy+hframe_th, sz+frame_width, -frame_width),
            (jamb_th+frame_width, jamb_th+width-frame_width, sy+hframe_th-inset, sz+frame_width, -frame_width),
        ]

        # vertices
        for sx, ex, y, sz, dab in steps:
            verts += [(sx, y, sz), (ex, y, sz)]
            for x, z in JVWindows._ellipse_iterator(a+dab, b+dab, res):
                verts.append((center_x+x, y, center_z+z))

        # faces
        JVWindows._loop_face_builder(len(steps), vpl, faces)
        JVWindows._close_glass_faces_in_loops(len(verts), vpl, faces, glass_ids)
        geometry_data.append((verts, faces, glass_ids))

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _polygon(props, mesh):
        geometry_data = []

        radius, jamb_w, jamb_th, sides = props.window_radius, props.jamb_width, Units.INCH, props.window_side_count
        frame_width, frame_th, inset = props.frame_width, props.frame_thickness, Units.Q_INCH  # pane variables
        interior_angle = ((sides - 2) * radians(180)) / sides

        # adjust so these are the widths/thicknesses perpendicular to the sides
        jamb_th /= sin(interior_angle / 2)
        frame_width /= sin(interior_angle / 2)

        ang_step = Euler((0, radians(360) / sides, 0))
        hjamb_w, hframe_th, = jamb_w / 2, frame_th / 2

        # jamb and pane
        steps = [  # one set of steps for the jamb, one set of steps for the pane
            (
                (radius, -hjamb_w), (radius+jamb_th, -hjamb_w), (radius+jamb_th, hjamb_w), (radius, hjamb_w)
            ),
            (
                (radius-frame_width, -hframe_th + inset), (radius-frame_width, -hframe_th),
                (radius, -hframe_th), (radius, hframe_th),
                (radius-frame_width, hframe_th), (radius-frame_width, hframe_th - inset)
            )
        ]

        for sub_steps in steps:
            verts, faces, glass_ids = [], [], []
            for rad, y in sub_steps:
                v = Vector((rad, 0, 0))
                for _ in range(sides):
                    verts.append((v[0], y, v[2]))
                    v.rotate(ang_step)

            JVWindows._loop_face_builder(len(sub_steps), sides, faces)
            geometry_data.append((verts, faces, glass_ids))

        # glass faces
        verts, faces, glass_ids = geometry_data[-1]  # pane entry
        JVWindows._close_glass_faces_in_loops(len(verts), sides, faces, glass_ids)

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _gothic(props, mesh):
        geometry_data = []

        width, height, jamb_w = props.window_width_medium, props.window_height_medium, props.jamb_width
        res, frame_width, frame_th = props.window_resolution // 2, props.frame_width, props.frame_thickness
        jamb_th = Units.INCH

        hframe_th, hjamb_w, hwidth, inset = frame_th / 2, jamb_w / 2, width / 2, Units.Q_INCH
        vpl = 2 + (res + 2) + (res + 1)  # two bottom, res + 2 on right side, res + 1 on left side
        level_z = height - hwidth*sqrt(3)  # the z value at which the arc begins (ignoring the thickness of the jamb)

        left_x = width + (2*jamb_th)
        cx = left_x / 2
        steps = [
            (  # start xz  start y    end x which is also the radius
                (jamb_th, -hjamb_w, jamb_th+width),
                (0, -hjamb_w, width+(2*jamb_th)),
                (0, hjamb_w, width+(2*jamb_th)),
                (jamb_th, hjamb_w, jamb_th+width),
            ),
            (
                (jamb_th+frame_width, -hframe_th+inset, jamb_th+width-frame_width),
                (jamb_th+frame_width, -hframe_th, jamb_th+width-frame_width),
                (jamb_th, -hframe_th, jamb_th+width),

                (jamb_th, hframe_th, jamb_th+width),
                (jamb_th+frame_width, hframe_th, jamb_th+width-frame_width),
                (jamb_th+frame_width, hframe_th-inset, jamb_th+width-frame_width)
            )
        ]
        # the centers of rotation are located at 0 and left_x and are on the outside of the jambs
        for substep in steps:
            verts, faces, glass_ids = [], [], []

            for sxz, sy, r in substep:
                verts += [(sxz, sy, sxz), (r, sy, sxz)]  # bottom two points

                # right side of arch
                for x, z in JVWindows._gothic_arc_iterator(r, cx, res):
                    verts.append((x, sy, z+level_z))

                iterator = iter(JVWindows._gothic_arc_iterator(r, cx, res, low_to_high=False))
                next(iterator)  # skip highest entry as the previous loop already got it
                for x, z in iterator:
                    verts.append((left_x-x, sy, z+level_z))

            JVWindows._loop_face_builder(len(substep), vpl, faces)
            geometry_data.append((verts, faces, glass_ids))

        # glass faces
        verts, faces, glass_ids = geometry_data[-1]  # get last entry which will be the pane's geometry
        JVWindows._close_glass_faces_in_loops(len(verts), vpl, faces, glass_ids)

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _ellipse(props, mesh):
        geometry_data = JVWindows._ellipse_worker(props.window_width_wide, props.window_height_short,
                                                  props.jamb_width, props.frame_width, props.window_resolution,
                                                  frame_th=props.frame_thickness)

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _circular(props, mesh):
        radius, res, jamb_w = props.window_radius, props.window_resolution, props.jamb_width
        ang = props.window_angle
        jamb_th, frame_width, frame_th, inset = Units.INCH, props.frame_width, props.frame_thickness, Units.Q_INCH

        hjamb_w, hframe_th = jamb_w / 2, frame_width / 2

        if props.full_circle:
            geometry_data = JVWindows._ellipse_worker(radius, radius, jamb_w, frame_width, res,
                                                      frame_th=frame_th, jamb_th=jamb_th, inset=inset)
        else:
            geometry_data = []
            start_angle, end_angle = ang - radians(180), -radians(180)  # start angle from -X axis
            hangle = (end_angle + start_angle) / 2

            steps = (
                (  # radius, y value  z value
                    (radius, -hjamb_w, jamb_th), (radius+jamb_th, -hjamb_w, 0),
                    (radius+jamb_th, hjamb_w, 0), (radius, hjamb_w, jamb_th)
                ),
                (
                    (radius-frame_width, -hframe_th+inset, jamb_th+frame_width),
                    (radius-frame_width, -hframe_th, jamb_th+frame_width),
                    (radius, -hframe_th, jamb_th),

                    (radius, hframe_th, jamb_th),
                    (radius-frame_width, hframe_th, jamb_th+frame_width),
                    (radius-frame_width, hframe_th-inset, jamb_th+frame_width),
                )
            )

            vpl = res + 3
            for substep in steps:
                verts, faces, glass_ids = [], [], []
                for rad, y, z in substep:
                    # determine the location of the center vertex
                    cv = Vector((z / sin(abs(hangle)), 0, 0))  # adjust z so cv[2]=z and x ends up between whatever
                    cv.rotate(Euler((0, hangle, 0)))  # rotate center vector to proper place

                    verts.append((cv[0], y, cv[2]))

                    # we have to clip the angles slightly because our center of radius is at (0, 0, 0), but we don't
                    # want to rotate all the way down to the axis for a point that is Z up from its
                    d_theta = asin(z / rad)
                    sa, ea = start_angle - d_theta, end_angle + d_theta
                    ang_step = Euler((0, (ea-sa) / (res + 1), 0))

                    v = Vector((rad, 0, 0))
                    v.rotate(Euler((0, sa, 0)))
                    for _ in range(res + 2):  # plus two for both end points
                        verts.append((v[0], y, v[2]))
                        v.rotate(ang_step)

                JVWindows._loop_face_builder(len(substep), vpl, faces)
                geometry_data.append((verts, faces, glass_ids))

            # glass ids
            verts, faces, glass_ids = geometry_data[-1]
            JVWindows._close_glass_faces_in_loops(len(verts), vpl, faces, glass_ids)

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _bow(props, mesh):
        jamb_w, frame_width, frame_th, jamb_th = props.jamb_width, props.frame_width, props.frame_thickness, Units.INCH
        angle_per_pane, radius = radians(180) / props.bow_segments, props.window_width_wide / 2
        pane_start_angle = (radians(180) - angle_per_pane) / 2  # how much the pane is rotated from the radius
        pane_width, height = 2 * radius * sin(angle_per_pane / 2), props.window_height_medium
        inset = Units.Q_INCH

        hjw = (jamb_w * cos(radians(90) - pane_start_angle)) / 2
        pane_center_radius = radius + (frame_th / 2)

        geometry_data = []
        corner_vector, angle_step = Vector((-radius, 0, 0)), Euler((0, 0, -angle_per_pane))
        cur_pane_angle = pane_start_angle

        inner_jamb, outer_jamb = Vector((-pane_center_radius+hjw, 0, 0)), Vector((-pane_center_radius-hjw, 0, 0))

        jamb_verts, jamb_faces = [], []
        # initial jamb vertices
        for x in (-pane_center_radius+hjw, -pane_center_radius-hjw):
            for z in (0, height + 2*jamb_th):
                jamb_verts.append((x, -jamb_th, z))

        for x in (-pane_center_radius+hjw, -pane_center_radius-hjw):
            for z in (jamb_th, height + jamb_th):
                jamb_verts.append((x, 0, z))

        for i in range(props.bow_segments):
            # create pane at +frame_th/2 so that the corner of the pane is at (0, 0, 0)
            verts, faces, glass_ids = JVWindows._rectangular_pane_geometry(pane_width, height, (0, frame_th/2, jamb_th),
                                                                           fw=frame_width, inset=inset,
                                                                           frame_th=frame_th)

            JVWindows._transform_vertex_positions(verts, rotation=Euler((0, 0, cur_pane_angle)),
                                                  after_translation=corner_vector)

            geometry_data.append((verts, faces, glass_ids))

            # vertical filler strips
            geometry_data.append(
                (*JVWindows._bay_bow_vertical_filler_strip(corner_vector, cur_pane_angle + radians(90),
                                                           angle_per_pane/2 if i == 0 else angle_per_pane,
                                                           height, frame_th, shift=(0, 0, jamb_th)),
                 []
                 ))

            # jamb vertices
            if i > 0:
                for bz, tz in ((0, height + 2*jamb_th), (jamb_th, jamb_th+height)):
                    for x, y in (inner_jamb[:2], outer_jamb[:2]):
                        jamb_verts.append((x, y, bz))
                        jamb_verts.append((x, y, tz))

            # move to next pane
            inner_jamb.rotate(angle_step)
            outer_jamb.rotate(angle_step)

            corner_vector.rotate(angle_step)
            cur_pane_angle -= angle_per_pane

        # last triangle filler
        geometry_data.append(
            (*JVWindows._bay_bow_vertical_filler_strip(corner_vector, 0, radians(90) - pane_start_angle,
                                                       height, frame_th, shift=(0, 0, jamb_th)), []))

        # last set of jamb vertices
        for x in (pane_center_radius-hjw, pane_center_radius+hjw):
            for z in (0, height + 2*jamb_th):
                jamb_verts.append((x, -jamb_th, z))

        for x in (pane_center_radius-hjw, pane_center_radius+hjw):
            for z in (jamb_th, height + jamb_th):
                jamb_verts.append((x, 0, z))

        # jamb faces
        JVWindows._bay_bow_jamb_faces(len(jamb_verts), jamb_faces, props.bow_segments)

        geometry_data.append((jamb_verts, jamb_faces, []))
        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _bay(props, mesh):
        width, height, pane_angle = props.window_width_wide, props.window_height_medium, props.bay_angle
        depth = props.window_depth
        jamb_w, jamb_th, frame_w, frame_th = props.jamb_width, Units.INCH, props.frame_width, props.frame_thickness
        inset = Units.Q_INCH

        pane_x = depth / tan(pane_angle)
        small_width, large_width = depth / sin(pane_angle), width - 2*pane_x
        geometry_data = []

        # panes
        for angle, pw, corner in (
            (pane_angle, small_width, Vector((-width/2, 0, 0))),  # left
            (0, large_width, Vector((-large_width/2, depth, 0))),  # middle
            (-pane_angle, small_width, Vector((large_width/2, depth, 0)))  # right
        ):
            verts, faces, glass_ids = JVWindows._rectangular_pane_geometry(pw, height, (0, frame_th/2, jamb_th),
                                                                           frame_th=frame_th, fw=frame_w, inset=inset)
            JVWindows._transform_vertex_positions(verts, Euler((0, 0, angle)), after_translation=corner)
            geometry_data.append((verts, faces, glass_ids))

        # end filler strips
        geometry_data.extend((
            (*JVWindows._bay_bow_vertical_filler_strip(Vector((-width/2, 0, 0)), radians(180) - pane_angle/2,
                                                       pane_angle/2, height, frame_th, shift=(0, 0, jamb_th)), []),
            (*JVWindows._bay_bow_vertical_filler_strip(Vector((width/2, 0, 0)), 0, pane_angle/2,
                                                       height, frame_th, shift=(0, 0, jamb_th)), [])
        ))

        # in between
        for x, angle in ((-large_width/2, radians(90)), (large_width/2, radians(90)-pane_angle)):
            geometry_data.append((
                *JVWindows._bay_bow_vertical_filler_strip(Vector((x, depth, 0)), angle, pane_angle, height, frame_th,
                                                          shift=(0, 0, jamb_th)), []
            ))

        # jamb
        hjw = (jamb_w * cos(radians(90)-pane_angle)) / 2
        jamb_verts, jamb_faces = [], []
        cx = width/2 + frame_th/2

        # starting jamb vertices
        for x in (-cx+hjw, -cx-hjw):
            for z in (0, height + 2*jamb_th):
                jamb_verts.append((x, -jamb_th, z))

        for x in (-cx+hjw, -cx-hjw):
            for z in (jamb_th, height + jamb_th):
                jamb_verts.append((x, 0, z))

        # main jamb vertices

        for corner, inside_sign in ((Vector((-large_width/2, depth, 0)), -1), (Vector((large_width/2, depth, 0)), 1)):
            inside = Vector((-inside_sign * (hjw - frame_th/2), 0, 0))
            outside = Vector((-inside_sign * (hjw+frame_th), 0, 0))

            inside.rotate(Euler((0, 0, inside_sign * pane_angle/2)))
            outside.rotate(Euler((0, 0, -inside_sign * (radians(90) + pane_angle/2))))

            inside += corner
            outside += corner

            for bz, tz in ((0, height + 2*jamb_th), (jamb_th, height+jamb_th)):
                for x, y in (inside[:2], outside[:2]):
                    jamb_verts.append((x, y, bz))
                    jamb_verts.append((x, y, tz))

        # closing jamb vertices
        for x in (cx-hjw, cx+hjw):
            for z in (0, height + 2*jamb_th):
                jamb_verts.append((x, -jamb_th, z))

        for x in (cx-hjw, cx+hjw):
            for z in (jamb_th, height + jamb_th):
                jamb_verts.append((x, 0, z))

        # jamb faces
        JVWindows._bay_bow_jamb_faces(len(jamb_verts), jamb_faces, 3)

        geometry_data.append((jamb_verts, jamb_faces, []))
        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    # WORKERS AND ITERATORS -------------------------------------------------------------------------------------
    @staticmethod
    def _bay_bow_jamb_faces(vertex_count: int, faces: list, sides: int):
        """
        Create the faces for the jamb on bay and bow windows
        :param vertex_count: the number of vertices that jamb contains
        :param faces: the list to add the faces to
        :param sides: the number of sides the window has
        """
        # jamb faces
        p = 0
        for _ in range(sides):
            faces.extend((
                (p, p+8, p+10, p+2), (p, p+8, p+12, p+4), (p+4, p+12, p+14, p+6), (p+2, p+6, p+14, p+10),
                (p+5, p+13, p+15, p+7), (p+5, p+13, p+9, p+1), (p+1, p+9, p+11, p+3), (p+3, p+7, p+15, p+11)
            ))

            p += 8

        # vertical jamb faces
        for p in (0, vertex_count-8):
            faces.extend((
                (p, p+1, p+3, p+2), (p, p+4, p+5, p+1), (p+2, p+3, p+7, p+6), (p+4, p+5, p+7, p+6)
            ))

    @staticmethod
    def _bay_bow_vertical_filler_strip(corner_v: Vector, start_angle: float, angle: float, height: float,
                                       frame_th: float, shift=(0, 0, 0)) -> Tuple[list, list]:
        """
        Create the triangular filler strip found between bay and bow windows. Return vertices and faces.
        :param corner_v: the location of the corner of the frame
        :param start_angle: the angle, measured from the +X axis, with positive being CCW of corner_v
        :param angle: how wide the angle is for the triangle
        :param height: the height of the strip
        :param frame_th: the thickness of the frame
        :param shift: Amount to add to all x, y, and z positions
        :return: the vertices and faces of the strip
        """
        verts, faces = [], []
        dx, dy, dz = shift

        v1 = Vector((frame_th, 0, 0))
        v2 = v1.copy()

        v1.rotate(Euler((0, 0, start_angle)))
        v2.rotate(Euler((0, 0, start_angle+angle)))

        for x, y in (corner_v[:2], (corner_v + v1)[:2], (corner_v + v2)[:2]):
            verts.append((dx+x, dy+y, dz))
            verts.append((dx+x, dy+y, dz+height))

        faces.extend(((0, 2, 3, 1), (2, 4, 5, 3), (4, 0, 1, 5), (1, 3, 5), (0, 4, 2)))

        return verts, faces

    @staticmethod
    def _ellipse_worker(a, b, jamb_w, frame_width, res, frame_th=Units.INCH, jamb_th=Units.INCH, inset=Units.Q_INCH):
        hjamb_w, hframe_th = jamb_w / 2, frame_th / 2
        res = res // 2
        vpl = res + 2 + res

        steps = (
            (  # ab_offset, y
                (0, -hjamb_w), (jamb_th, -hjamb_w),
                (jamb_th, hjamb_w), (0, hjamb_w)
            ),
            (
                (-frame_width, -hframe_th + inset), (-frame_width, -hframe_th), (0, -hframe_th),
                (0, hframe_th), (-frame_width, hframe_th), (-frame_width, hframe_th - inset)
            )
        )

        geometry_data = []
        for substep in steps:
            verts, faces, glass_ids = [], [], []

            for ab_offset, yy in substep:
                p = len(verts)

                # lower half
                for x, z in JVWindows._ellipse_iterator(a + ab_offset, b + ab_offset, res):
                    verts.append((x, yy, z))  # negative because points are generate in CCW order, so flip side

                # top half
                for x, y, z in verts[-2:p:-1]:  # get all except end two points in reverse order
                    verts.append((x, y, -z))

            JVWindows._loop_face_builder(len(substep), vpl, faces)
            geometry_data.append((verts, faces, glass_ids))

        verts, faces, glass_ids = geometry_data[-1]
        JVWindows._close_glass_faces_in_loops(len(verts), vpl, faces, glass_ids)

        return geometry_data

    @staticmethod
    def _rectangular_jamb_geometry(width: float, height: float, start_coord: tuple, jamb_width: float, keep_left=True,
                                   th=Units.INCH) -> Tuple[list, list, list]:
        """
        Create a rectangular jamb and return the vertex and face geometry
        :param width: the width of the jamb (inside dimensions)
        :param height: the height of the jamb (inside dimensions)
        :param start_coord: the starting x, y, z coordinate
        :param jamb_width: the width of the jamb
        :param keep_left: whether or not to build the left side of the jamb
        :return: the vertex, face, and glass id lists
        """
        verts, faces, glass_ids = [], [], []
        hj = jamb_width / 2

        if keep_left:
            dx = th
        else:
            dx = 0

        x, y, z = start_coord
        for yy in (y-hj, y+hj):
            verts += [  # outer loop followed by inner loop
                (x, yy, z), (x+th+width+th, yy, z), (x+th+width+th, yy, z+th+height+th), (x, yy, z+th+height+th),
                (x+dx, yy, z+th), (x+th+width, yy, z+th), (x+th+width, yy, z+th+height), (x+dx, yy, z+th+height)
            ]

        # faces only front and back
        for p in (0, 8):
            for _ in range(3):
                faces.append((p, p+1, p+5, p+4))
                p += 1

            if keep_left:
                faces.append((p, p-3, p+1, p+4))

        # outside faces
        p = 0
        for _ in range(3):
            faces.append((p, p+8, p+9, p+1))
            p += 1

        # inside faces
        p = 4
        for _ in range(3):
            faces.append((p, p+8, p+9, p+1))
            p += 1

        # outside and inside face on left
        if keep_left:
            faces.append((0, 8, 11, 3))
            faces.append((4, 12, 15, 7))

        return verts, faces, glass_ids

    @staticmethod
    def _rectangular_pane_geometry(w: float, h: float, start_coord: tuple, frame_th=1.5*Units.INCH, inset=Units.Q_INCH,
                                   fw=Units.INCH) -> Tuple[list, list, list]:
        """
        Create the geometry needed to build a rectangular window pane
        :param w: the width of the pane
        :param h: the height of the pane
        :param start_coord: the start coordinate
        :param frame_th: the thickness of the pane
        :param inset: how much to inset when going from the frame to glass part of the pane
        :param fw: thick the frame of the pane is
        :return:
        """
        verts, faces, glass_ids = [], [], []
        x, y, z = start_coord
        fy, gy = frame_th / 2, (frame_th - (2*inset)) / 2  # half of the frame y and half of the glass y

        # start with inset-glass vertices then move out and around, ending at inset-glass vertices on the other side
        verts += [
            (x+fw, y-gy, z+fw), (x+w-fw, y-gy, z+fw), (x+w-fw, y-gy, z+h-fw), (x+fw, y-gy, z+h-fw),
            (x+fw, y-fy, z+fw), (x+w-fw, y-fy, z+fw), (x+w-fw, y-fy, z+h-fw), (x+fw, y-fy, z+h-fw),
            (x, y-fy, z), (x+w, y-fy, z), (x+w, y-fy, z+h), (x, y-fy, z+h),

            (x, y+fy, z), (x+w, y+fy, z), (x+w, y+fy, z+h), (x, y+fy, z+h),
            (x+fw, y+fy, z+fw), (x+w-fw, y+fy, z+fw), (x+w-fw, y+fy, z+h-fw), (x+fw, y+fy, z+h-fw),
            (x+fw, y+gy, z+fw), (x+w-fw, y+gy, z+fw), (x+w-fw, y+gy, z+h-fw), (x+fw, y+gy, z+h-fw),
        ]

        JVWindows._loop_face_builder(6, 4, faces)
        faces.append((0, 1, 2, 3))
        p = len(verts) - 4
        faces.append((p, p+1, p+2, p+3))
        glass_ids.extend((len(faces) - 1, len(faces) - 2))

        return verts, faces, glass_ids

    @staticmethod
    def _ellipse_iterator(a, b, res) -> Tuple[float, float]:
        """
        For an half-ellipse with x-axis radius of 'a' and y-axis radius of 'b' and the given resolution, return
        the x, y coordinates of each point. Points are iterator in counter-clockwise fashion
        :param a: the x-axis radius
        :param b: the y-axis radius
        :param res: (res + 2) points will be generated on the ellipse
        :return: x, y points on the half-ellipse
        """
        ang_step = radians(180) / (res + 1)

        theta = 0
        for _ in range(res + 2):  # two extra for end points
            x, y = a*cos(theta), b*sin(theta)

            yield (x, y)
            theta += ang_step

    @staticmethod
    def _gothic_arc_iterator(radius, cx, res, low_to_high=True) -> Tuple[float, float]:
        """
        Generate (x, z) points on one side of a gothic arc with the given radius.
        :param radius: the radius of the circle that forms the arc
        :param cx: the x value of the center of the window
        :param res: the number of segments on the arc, barring the start and end point
        :param low_to_high: whether to start at the center and work outwards, or to start level and work to the top
        :return a tuple of the (x, z) coordinates where x and z are the offset from the center of the arc
        """
        # make angles negative because of how CCW rotation is negative in Blender
        start_angle, end_angle = 0, -acos(cx / radius)

        if not low_to_high:  # swap order if not low to high
            start_angle, end_angle = end_angle, start_angle

        ang_step = Euler((0, (end_angle - start_angle) / (res + 1), 0))

        v = Vector((radius, 0, 0))
        v.rotate(Euler((0, start_angle, 0)))

        for _ in range(res + 2):
            yield (v[0], v[2])  # shift x to be centered around x=0

            v.rotate(ang_step)

    @staticmethod
    def _loop_face_builder(num_loops, vpl, faces):
        """
        Generate faces assuming that the vertices are indexed in counter-clockwise loops such that L0 can be connected
        to the corresponding vertices in L1. The last two loops have to be joined differently as their isn't the same
        offset
        :param num_loops: number of vertex loops
        :param vpl: number of vertices per loop
        :param faces: the list to add the faces to
        """
        p = 0
        # first num_loops - 1 loops will follow same pattern
        for _ in range(num_loops-1):
            for _ in range(vpl-1):  # last face in loop has to be manually connected
                faces.append((p, p+vpl, p+vpl+1, p+1))
                p += 1
            faces.append((p, p+vpl, p+1, p+1-vpl))  # last face in loop
            p += 1

        # connect 4th loop to 1st loop
        p, e = 0, (num_loops-1) * vpl  # first vertex index and index of vertex at the start of the last loop
        for _ in range(vpl-1):
            faces.append((p, e, e+1, p+1))
            e += 1
            p += 1
        faces.append((p, e, e+1-vpl, p+1-vpl))  # last face

    @staticmethod
    def _close_glass_faces_in_loops(v_len: int, vpl: int, faces: list, glass_ids: list):
        """
        Many of the windows are built by creating the jamb then the pane with sequential vertex loops. There will be
        six loops for the pane, with the first loop forming the inside piece of glass, and the last loop forming the
        outside piece of glass. Calculate those faces.
        :param v_len: The number of vertices currently created
        :param vpl: The number of vertices per vertex loop
        :param faces: the list of faces
        :param glass_ids: the list of face indices that need to have the glass material
        """
        p = v_len - (6 * vpl)  # go back to start of first pane loop
        faces.append([i for i in range(p, p + vpl)])
        p = v_len - vpl
        faces.append([i for i in range(p, p + vpl)])

        glass_ids.extend((len(faces) - 1, len(faces) - 2))
