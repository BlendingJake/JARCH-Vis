from math import atan, radians, acos
from typing import List, Set, Tuple

from mathutils import Vector, Euler
from bmesh.types import BMEdge
from bpy.types import MeshPolygon, MeshVertex

from .jv_common_classes import BisectingPlane
from .jv_properties import FaceGroup


class CuboidalRegion:
    """A representation of a cube-shaped region defined by six planes.
    Can be used to tell if a point is contained within the cube.
    """

    def __init__(
        self,
        planes: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
    ):
        """Take a list of the defining planes. Each plane is defined by a
        point on that plane and its normal. All plane normals should point
        towards the center of the cube.

        :param planes: tuples of (point on plane, plane normal)
        """
        self.planes = [
            (Vector(po), Vector(no)) for po, no in planes
        ]  # convert to vectors for easier math later

    def __contains__(self, item: Vector):
        """Determine if the item/point is in the cube by determining if it is
        on the positive sides of all the planes using the dot product.

        :param item: a Vector to check whether or not it is in the plane
        :return: a boolean indicating whether the point is in the cube or not
        """
        for pos, normal in self.planes:
            if normal.dot(item - pos) < 0:
                return False
        else:
            return True


def determine_face_group_scale_rot_loc(
    faces: List[MeshPolygon], vertices: List[MeshVertex], fg: FaceGroup
):
    """Determine the rotation of the faces from a plane lying in the X-Y
    plane with normal (0, 0, 1). Rotate the face points into the X-Y plane
    using that rotation and then determine the offset of the bottom-left
    corner from the origin and the X-Y dimensions of the faces.

    :param faces: the list of polygons that make up the face group
    :param vertices: the list of vertices that make up the face group
    :param fg: the face group to assign the rot, loc, and dim values to
    """
    normal = faces[0].normal.copy()

    # Determine how much you have to rotate to go from the +Z axis to the normal
    # vector. theta = rotation on x-axis. atan is defined from (-90, 90), modify
    # rotation to be from +Y axis not +X

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
    vertex_vectors = [v.co.copy() for v in vertices]
    for v in vertex_vectors:
        v.rotate(inv_rot1)
        v.rotate(inv_rot2)

    # DIMENSIONS and LOCATION
    min_x, min_y, min_z = vertex_vectors[0]
    max_x, max_y, max_z = vertex_vectors[0]

    for vert in vertex_vectors:
        min_x = min(min_x, vert[0])
        max_x = max(max_x, vert[0])

        min_y = min(min_y, vert[1])
        max_y = max(max_y, vert[1])

        min_z = min(min_z, vert[2])
        max_z = max(max_z, vert[2])

    # ultimately ignore z as the points have been rotated into the X-Y plane
    fg.rotation = rot
    fg.dimensions = (max_x - min_x, max_y - min_y)

    loc = Vector((min_x, min_y, min_z))
    loc.rotate(Euler((rho, 0, 0)))
    loc.rotate(Euler((0, 0, theta)))

    fg.location = loc


def determine_bisecting_planes(
    edges: Set[BMEdge], vertices: Set[MeshVertex], fg: FaceGroup, normal: Vector
):
    """Calculate the normal and center vectors for every boundary edge where
    the normal will point towards the center of the face group. The normal and
    center vectors will be added to ``fg`` and can later be used to create
    planes to bisect the mesh and cut its outline.

    :param edges: The set of boundary edges for the face group
    :param vertices: All vertices in the face group
    :param fg: The face group itself to update with the bisecting
        plane center and normal.
    :param normal: The normal of the faces in the face group
    """
    face_group_center = Vector()
    for vertex in vertices:
        face_group_center += vertex.co
    face_group_center /= len(vertices)

    for edge in edges:
        (
            v1,
            v2,
        ) = (
            edge.verts[0].co,
            edge.verts[1].co,
        )
        edge_v = Vector((v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]))

        bisecting_plane: BisectingPlane = fg.bisecting_planes.add()
        edge_center = Vector(
            ((v2[0] + v1[0]) / 2, (v2[1] + v1[1]) / 2, (v2[2] + v1[2]) / 2)
        )
        bisecting_plane.center = edge_center

        # The cross product of the edge and the normal of the face will be
        # perpendicular to both and in the plane
        edge_normal = edge_v.cross(normal)
        edge_normal_neg = edge_normal.copy()
        edge_normal_neg.negate()

        # See if the edge_normal or it's inverse is closer to the center of
        # the faces. Pick the one closer
        discerner = bisecting_plane.center - face_group_center + normal
        if edge_normal.angle(discerner) < edge_normal_neg.angle(discerner):
            edge_normal = edge_normal_neg

        bisecting_plane.normal = edge_normal
