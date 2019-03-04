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

from mathutils import Vector, Euler
from typing import List, Tuple
from bpy.types import MeshPolygon, MeshVertex
from math import atan, radians, acos


class Units:
    FOOT: float = 1 / 3.248
    INCH: float = FOOT / 12
    TQ_INCH: float = INCH * 0.75  # 3/4 inch
    H_INCH: float = INCH / 2  # 1/2 inch
    Q_INCH: float = H_INCH / 2  # 1/4 inch
    ETH_INCH: float = INCH / 8  # 1/8th inch
    STH_INCH: float = INCH / 16  # 1/16th inch


class CuboidalRegion:
    """
    A representation of a cube-shaped region defined by six planes. Can be used to tell if a point is contained
    within the cube.
    """
    def __init__(self, planes: List[Tuple[tuple, tuple]]):
        """
        Take a list of the defining planes. Each plane is defined by a point on that plane and its normal.
        All plane normals should point towards the center of the cube.
        :param planes: tuples of (point on plane, plane normal)
        """
        self.planes = [(Vector(po), Vector(no)) for po, no in planes]  # convert to vectors for easier math later

    def __contains__(self, item):
        """
        Determine if the item/point is in the cube by determining if it is on the positive sides of all the planes using
        the dot product.
        :param item: a Vector to check whether or not it is in the plane
        :return: a boolean indicating whether the point is in the cube or not
        """
        for pos, normal in self.planes:
            if normal.dot(item - pos) < 0:
                return False
        else:
            return True


def determine_face_group_scale_rot_loc(faces: List[MeshPolygon], vertices: List[MeshVertex], fg):
    """
    Determine the rotation of the faces from a plane lying in the X-Y plane with normal (0, 0, 1).
    Rotate the face points into the X-Y plane using that rotation and then determine the offset of the
    bottom-left corner from the origin and the X-Y dimensions of the faces
    :param faces: a list of bpy.types.MeshPolygons that make up the face group
    :param vertices: a list of bpy.types.MeshVertexs that make up the face group
    :param fg: the face group to assign the rot, loc, and dim values to
    """
    # ROTATION - the amount of rotation needed to get a point in X-Y plane to the face
    normal = Vector(faces[0].normal)

    # determine how much you have to rotate to go from the +Z axis to the normal vector
    # theta = rotation on x-axis. atan is defined from (-90, 90), modify rotation to be from +Y axis not +X
    if normal[0] != 0:
        theta = atan(normal[1] / normal[0])
        if normal[0] < 0:
            theta -= radians(90)
        else:
            theta += radians(90)

    else:  # either on +Y or -Y axis
        if normal[1] > 0:
            theta = radians(180)
        else:
            theta = 0

    rho = acos(normal[2])
    rot = Euler((rho, 0, theta))

    # determine how much you have to go to rotate all the points into the X-Y plane
    # do z rotation before x rotation to ensure everything ends up properly
    inv_rot1 = Euler((0, 0, -theta))
    inv_rot2 = Euler((-rho, 0, 0))

    # rotate all points into the X-Y plane
    vertices = [Vector(v.co) for v in vertices]
    for v in vertices:
        v.rotate(inv_rot1)
        v.rotate(inv_rot2)

    # DIMENSIONS and LOCATION
    min_x, min_y, min_z, max_x, max_y, max_z = *vertices[0], *vertices[0]
    for vert in vertices:
        min_x = min(min_x, vert[0])
        max_x = max(max_x, vert[0])

        min_y = min(min_y, vert[1])
        max_y = max(max_y, vert[1])

        min_z = min(min_z, vert[2])
        max_z = max(max_z, vert[2])

    # ultimately ignore z as the points have been rotated into the X-Y plane
    fg.rotation = rot
    fg.dimensions = (max_x-min_x, max_y-min_y)

    loc = Vector((min_x, min_y, min_z))
    loc.rotate(Euler((rho, 0, 0)))
    loc.rotate(Euler((0, 0, theta)))

    fg.location = loc


def determine_bisecting_planes(edges: set, vertices: set, fg, normal: Vector):
    """
    Calculate vectors that are in the plane of the face group, perpendicular to the edge, and pointer inward
    :param edges: the set of boundary edges for the face group (bmesh.types.BMEdge)
    :param vertices: all vertices in the face group (bpy.types.MeshVertex)
    :param fg: the face group itself
    :param normal: the normal of the faces in the face group
    """
    face_group_center = Vector((0, 0, 0))
    for vertex in vertices:
        face_group_center += Vector(vertex.co)
    face_group_center /= len(vertices)

    for edge in edges:
        v1, v2, = edge.verts[0].co, edge.verts[1].co
        edge_v = Vector((v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]))

        bisecting_plane = fg.bisecting_planes.add()
        edge_center = Vector(((v2[0]+v1[0]) / 2, (v2[1]+v1[1]) / 2, (v2[2]+v1[2]) / 2))
        bisecting_plane.center = edge_center

        # the cross product of the edge and the normal of the face will be perpendicular to both and in the plane
        edge_normal = edge_v.cross(normal)
        edge_normal_neg = edge_normal.copy()
        edge_normal_neg.negate()

        # see if the edge_normal or it's inverse is closer to the center of the faces. Pick the one closer
        discerner = Vector(bisecting_plane.center) - face_group_center + normal
        if edge_normal.angle(discerner) < edge_normal_neg.angle(discerner):
            edge_normal = edge_normal_neg

        bisecting_plane.normal = edge_normal
