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
from math import sqrt, radians, acos, sin
from mathutils import Vector, Euler
from . jv_builder_base import JVBuilderBase
from . jv_utils import Units
from typing import Tuple, List


class JVWindows(JVBuilderBase):
    is_convertible = False

    @staticmethod
    def draw(props, layout):
        layout.prop(props, "window_pattern", icon="MOD_WIREFRAME")

        if props.window_pattern in ("regular", "arch", "gothic"):
            layout.separator()
            row = layout.row()
            row.prop(props, "window_width_medium")
            row.prop(props, "window_height_medium")
        elif props.window_pattern == "polygon":
            layout.separator()
            layout.prop(props, "window_radius")

        layout.separator()
        layout.prop(props, "jamb_width")

        layout.separator()
        layout.prop(props, "frame_width")

        if props.window_pattern in ("regular", "arch"):
            layout.separator()
            layout.prop(props, "slider", icon="DECORATE_OVERRIDE")

            if props.slider and props.window_pattern == "regular":
                layout.prop(props, "orientation", icon="ORIENTATION_VIEW")

        if props.window_pattern == "polygon":
            layout.separator()
            layout.prop(props, "window_side_count")

        if props.window_pattern == "arch":
            layout.separator()
            layout.prop(props, "window_roundness")

        if props.window_pattern in ("arch", "gothic"):
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
        frame_width, pane_th, jamb_th = props.frame_width, 1.5 * Units.INCH, Units.INCH

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
                                                                      th=pane_th, pad=frame_width))

            # # create second pane if needed
            if props.slider:
                y += pane_th
                if props.orientation == "vertical":
                    z += pane_height - frame_width
                else:
                    x += pane_width - frame_width

                geometry_data.append(JVWindows._rectangular_pane_geometry(pane_width, pane_height, (x+jamb_th, y, z),
                                                                          th=pane_th, pad=frame_width))

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
        frame_width, jamb_th, frame_th, inset = props.frame_width, Units.INCH, Units.INCH, Units.Q_INCH

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
                                                                      pad=frame_width, inset=inset,
                                                                      th=frame_th))

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
        p = len(verts)
        for sx, ex, y, sz, dab in steps:
            verts += [(sx, y, sz), (ex, y, sz)]
            for x, z in JVWindows._ellipse_iterator(a+dab, b+dab, res):
                verts.append((center_x+x, y, center_z+z))

        # faces
        JVWindows._loop_face_builder(len(steps), vpl, faces)
        faces.append([i for i in range(p, p+vpl, 1)])  # -Y glass face
        faces.append([i for i in range(len(verts) - vpl, len(verts), 1)])  # +Y glass face

        glass_ids.extend((len(faces) - 2, len(faces) - 1))
        geometry_data.append((verts, faces, glass_ids))

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _polygon(props, mesh):
        geometry_data = []

        radius, jamb_w, jamb_th, sides = props.window_radius, props.jamb_width, Units.INCH, props.window_side_count
        frame_width, frame_th, inset = props.frame_width, Units.INCH, Units.Q_INCH  # pane variables

        ang_step = Euler((0, radians(360) / sides, 0))
        hjamb_w, hframe_th, = jamb_w / 2, frame_th / 2

        # jamb and pane
        steps = [  # one set of steps for the jamb, one set of steps for the pane
            (
                (radius, -hjamb_w), (radius+jamb_th, -hjamb_w), (radius+jamb_th, hjamb_w), (radius, hjamb_w)
            ),
            (
                (radius - frame_width, -hframe_th + inset), (radius - frame_width, -hframe_th),
                (radius, -hframe_th), (radius, hframe_th),
                (radius - frame_width, hframe_th), (radius - frame_width, hframe_th - inset)
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
        p = len(verts) - (6 * sides)  # go back to start of first pane loop
        faces.append([i for i in range(p, p+sides)])
        p = len(verts) - sides
        faces.append([i for i in range(p, p+sides)])

        glass_ids.extend((len(faces) - 1, len(faces) - 2))

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

    @staticmethod
    def _gothic(props, mesh):
        geometry_data = []

        width, height, jamb_w = props.window_width_medium, props.window_height_medium, props.jamb_width
        res, frame_width, frame_th, jamb_th = props.window_resolution // 2, props.frame_width, Units.INCH, Units.INCH

        hframe_th, hjamb_w, hwidth, cx, inset = frame_th / 2, jamb_w / 2, width / 2, jamb_th + (width / 2), Units.Q_INCH
        vpl = 2 + (res + 2) + (res + 1)  # two bottom, res + 2 on right side, res + 1 on left side

        steps = [
            # start x, start y,  start z,      end x,   height, half_width
            (  # jamb
                (jamb_th, -hjamb_w, jamb_th, jamb_th+width, height, hwidth),
                (0, -hjamb_w, 0, width + (2*jamb_th), height + (2*jamb_th), hwidth+jamb_th),
                (0, hjamb_w, 0, width + (2*jamb_th), height + (2*jamb_th), hwidth+jamb_th),
                (jamb_th, hjamb_w, jamb_th, jamb_th+width, height, hwidth)
            ), (  # pane
                (jamb_th+frame_width, -hframe_th+inset, jamb_th+frame_width, jamb_th+width-frame_width,
                 height-frame_width, hwidth-frame_width),
                (jamb_th+frame_width, -hframe_th, jamb_th+frame_width, jamb_th+width-frame_width, height-frame_width,
                 hwidth-frame_width),
                (jamb_th, -hframe_th, jamb_th, jamb_th + width, height, hwidth),

                (jamb_th, hframe_th, jamb_th, jamb_th + width, height, hwidth),
                (jamb_th+frame_width, hframe_th, jamb_th+frame_width, jamb_th+width-frame_width, height-frame_width,
                 hwidth-frame_width),
                (jamb_th+frame_width, hframe_th-inset, jamb_th+frame_width, jamb_th+width-frame_width,
                 height-frame_width, hwidth-frame_width)
            )
        ]
        for substep in steps:
            verts, faces, glass_ids = [], [], []

            for sx, sy, sz, ex, h, hw in substep:
                verts += [(sx, sy, sz), (ex, sy, sz)]  # bottom two points

                # right side of arch
                for x, z in JVWindows._gothic_arch_iterator(h, hw, res):
                    verts.append((cx+x, sy, z))

                iterator = iter(JVWindows._gothic_arch_iterator(h, hw, res, low_to_high=False))
                next(iterator)  # skip highest entry as the previous loop already got it
                for x, z in iterator:
                    verts.append((cx-x, sy, z))

            JVWindows._loop_face_builder(len(substep), vpl, faces)
            geometry_data.append((verts, faces, glass_ids))

        JVWindows._update_mesh_from_geometry_lists(mesh, geometry_data)

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
    def _rectangular_pane_geometry(w: float, h: float, start_coord: tuple, th=1.5 * Units.INCH, inset=Units.Q_INCH,
                                   pad=Units.INCH) -> Tuple[list, list, list]:
        """
        Create the geometry needed to build a rectangular window pane
        :param w: the width of the pane
        :param h: the height of the pane
        :param start_coord: the start coordinate
        :param th: the thickness of the pane
        :param inset: how much to inset when going from the frame to glass part of the pane
        :param pad: thick the frame of the pane is
        :return:
        """
        verts, faces, glass_ids = [], [], []
        x, y, z = start_coord
        fy, gy = th / 2, (th - (2*inset)) / 2  # half of the frame y and half of the glass y

        # start with inset-glass vertices then move out and around, ending at inset-glass vertices on the other side
        verts += [
            (x+pad, y-gy, z+pad), (x+w-pad, y-gy, z+pad), (x+w-pad, y-gy, z+h-pad), (x+pad, y-gy, z+h-pad),
            (x+pad, y-fy, z+pad), (x+w-pad, y-fy, z+pad), (x+w-pad, y-fy, z+h-pad), (x+pad, y-fy, z+h-pad),
            (x, y-fy, z), (x+w, y-fy, z), (x+w, y-fy, z+h), (x, y-fy, z+h),

            (x, y+fy, z), (x+w, y+fy, z), (x+w, y+fy, z+h), (x, y+fy, z+h),
            (x+pad, y+fy, z+pad), (x+w-pad, y+fy, z+pad), (x+w-pad, y+fy, z+h-pad), (x+pad, y+fy, z+h-pad),
            (x+pad, y+gy, z+pad), (x+w-pad, y+gy, z+pad), (x+w-pad, y+gy, z+h-pad), (x+pad, y+gy, z+h-pad),
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
        :param res: the resolution/number of points returns for the half-ellipse
        :return: x, y points on the half-ellipse
        """
        x_step = (2*a) / (res+1)
        x = a
        for _ in range(res + 2):  # two extra for end points
            y = sqrt(1 - min(1, x**2 / a**2)) * b  # rounding errors can cause x**2 / a**2 > 1

            yield x, y
            x -= x_step

    @staticmethod
    def _gothic_arch_iterator(height, half_width, res, low_to_high=True) -> Tuple[float, float]:
        """
        Generate (x, z) coordinates for a gothic arch centered around x=0, z=0, with the center of the radius
        at -half_width on the X-axis and (res + 2) number over vertices.
        :param height: The total height of the gothic style window
        :param half_width: half the width of the window, aka the distance from the center to the edge
        :param res: the number of segments to insert on the arch. The actual number will be res + 2 for start and end
        :param low_to_high: whether to start at the edge of the window and rotate to the center, or vice-versa
        :return: (x, z) points offset from the center of the window on the x-axis and 0 on the z-axis
        """
        r = half_width * 2
        # make angles negative because of how CCW rotation is negative in Blender
        start_angle, end_angle = -0, -acos(half_width / r)
        below_split = height - (r * sin(-end_angle))  # height below arc split

        if not low_to_high:  # swap order if not low to high
            start_angle, end_angle = end_angle, start_angle

        ang_step = Euler((0, (end_angle - start_angle) / (res + 1), 0))

        v = Vector((r, 0, 0))
        v.rotate(Euler((0, start_angle, 0)))

        for _ in range(res + 2):
            yield (v[0]-half_width, v[2]+below_split)  # shift x to be centered around x=0

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