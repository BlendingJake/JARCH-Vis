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

from . jv_builder_base import JVBuilderBase
from . jv_utils import Units
from typing import Tuple, List


class JVWindows(JVBuilderBase):
    is_convertible = False

    @staticmethod
    def draw(props, layout):
        layout.prop(props, "window_pattern", icon="MOD_WIREFRAME")

        if props.window_pattern == "regular":
            layout.separator()
            row = layout.row()
            row.prop(props, "window_width_medium")
            row.prop(props, "window_height_medium")

        layout.separator()
        layout.prop(props, "jamb_width")

        layout.separator()
        layout.prop(props, "frame_width")

        if props.window_pattern == "regular":
            layout.separator()
            layout.prop(props, "slider", icon="DECORATE_OVERRIDE")

            if props.slider:
                layout.prop(props, "orientation", icon="ORIENTATION_VIEW")

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

        p = 0
        for _ in range(5):
            for _ in range(3):
                faces.append((p, p+4, p+5, p+1))
                p += 1
            faces.append((p, p+4, p+1, p-3))
            p += 1

        # close faces on first and last loops
        faces.append((0, 1, 2, 3))
        p = len(verts) - 4
        faces.append((p, p+1, p+2, p+3))

        # add the indices of the glass faces which are the last two
        glass_ids.extend((len(faces) - 1, len(faces) - 2))

        return verts, faces, glass_ids
