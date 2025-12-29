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

from math import radians, atan
from random import uniform
from typing import Callable, Dict, Iterable, List, Literal, Set, Tuple, Union

from bpy.types import Context, Mesh, Object, UILayout
from bmesh.types import BMEdge, BMFace, BMVert, BMesh
from mathutils import Euler, Matrix, Vector

import bmesh
import bpy

from .jv_properties import JVProperties
from .jv_utils import CuboidalRegion


Geometry = List[Union[BMEdge, BMFace, BMVert]]
VecTuple = Tuple[float, float, float]


class JVBuilderBase:
    is_cutable = False
    """Whether the object supports cutouts"""

    is_convertible = False
    """Whether the object can be converted from FaceGroups"""

    @staticmethod
    def draw(props: JVProperties, layout: UILayout):
        pass

    @staticmethod
    def update(props: JVProperties, context: Context):
        pass

    @staticmethod
    def delete(props: JVProperties, context: Context):
        src: Object = props.convert_source_object

        if src is not None:  # remove boolean objects if non-convex face groups
            for fg in src.jv_properties.face_groups:
                if not fg.is_convex:
                    fg.boolean_object.hide_viewport = False
                    fg.boolean_object.select_set(True)

        bpy.ops.object.delete()

        if src is not None:
            src.hide_viewport = False
            src.select_set(True)
            if context.view_layer is not None:
                context.view_layer.objects.active = src

    @staticmethod
    def _start(context: Context):
        bm = bmesh.new()
        return bm

    @staticmethod
    def _uv_unwrap(by_seams=True):
        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.select_all(action="SELECT")

        if by_seams:
            bpy.ops.uv.unwrap(method="ANGLE_BASED", margin=0.001)
        else:
            bpy.ops.uv.smart_project()

        bpy.ops.object.editmode_toggle()

    @staticmethod
    def _finish(context: Context, bm: BMesh):
        if context.object is None or not isinstance(context.object.data, Mesh):
            return

        bm.normal_update()
        bm.to_mesh(context.object.data)
        bm.free()

    @staticmethod
    def _geometry(props: JVProperties, dims: tuple):
        return [], []

    @staticmethod
    def _build_mesh_from_geometry(
        mesh: BMesh,
        vertices: List[VecTuple],
        faces: List[Tuple[int, ...]],
    ):
        """Take a bmesh mesh, vertices positions, and face-vertex indices and clear
        and add the vertices and faces to the mesh object.

        :param mesh: The bmesh object to clear and add the geometry to
        :param vertices: Tuples of the positions of the vertices
        :param faces: Tuples of the indices of the vertices that make up the face
        """
        mesh.clear()
        for v in vertices:
            mesh.verts.new(v)
        mesh.verts.ensure_lookup_table()

        for f in faces:
            mesh.faces.new([mesh.verts[i] for i in f])
        mesh.faces.ensure_lookup_table()

    @staticmethod
    def _solidify(mesh: BMesh, thickness: Union[Callable[[], float], float]):
        """Solidify the mesh. If 'thickness' is callable, then use the normal
        as the direction.

        :param mesh: The mesh to solidify
        :param thickness: If thickness is callable, then each new face gets a
            thickness value from the function. Otherwise, the value will be
            used consistently.
        """
        mesh.normal_update()
        start_th = 0 if callable(thickness) else thickness

        new_geom: Geometry = bmesh.ops.solidify(
            mesh, geom=mesh.faces[:], thickness=start_th
        )["geom"]

        # manually add thickness if 'thickness' is callable
        if callable(thickness):
            faces = set()
            for item in new_geom:
                if isinstance(item, BMFace):
                    faces.add(item)

            groups = JVBuilderBase._group_connected_faces(faces)
            visited = set()
            for group in groups:
                th = thickness()
                for face in group:
                    for v in face.verts:
                        if v not in visited:
                            v.co.x += face.normal[0] * th
                            v.co.y += face.normal[1] * th
                            v.co.z += face.normal[2] * th

                            visited.add(v)

        return new_geom

    @staticmethod
    def _create_variance_function(vary: bool, base_amount: float, variance: float):
        variance /= 100  # convert to decimal

        def _vary():
            if not vary:
                return base_amount

            return uniform(base_amount * (1 - variance), base_amount * (1 + variance))

        return _vary

    @staticmethod
    def _cut_meshes(
        meshes: List[BMesh],
        planes: List[Tuple[VecTuple, VecTuple]],
        fill_holes=False,
        remove_geom=True,
    ):
        """Take the bmesh object and bisect it with all the planes given and
        remove the geometry outside of the planes.

        :param meshes: A list of the meshes to cut
        :param planes: A list of tuples, each tuple being (plane position,
            plane normal). The normals should point towards the center of the
            mesh, aka, geometry on the opposite side of the normal will be removed
        """
        for mesh in meshes:
            for plane in planes:
                pos, normal = plane
                geom = bmesh.ops.bisect_plane(
                    mesh,
                    geom=[*mesh.faces, *mesh.edges, *mesh.verts],
                    dist=0.001,
                    plane_co=pos,
                    plane_no=normal,
                    clear_inner=remove_geom,
                )

                if fill_holes:
                    JVBuilderBase._fill_holes(mesh, geom["geom_cut"])

            mesh.faces.ensure_lookup_table()
            mesh.edges.ensure_lookup_table()
            mesh.verts.ensure_lookup_table()

    @staticmethod
    def _fill_holes(mesh: BMesh, cut_geometry: Geometry):
        """Given a mesh and geometry generated by using bisect_plane,
        fill the holes/ends.

        :param mesh: The mesh to operate on
        :param cut_geometry: A list of the new vertices, edges, and faces
            created by bisecting the mesh.
        """
        edges: Set[BMEdge] = set()
        verts: Set[BMVert] = set()
        for item in cut_geometry:
            if isinstance(item, BMEdge):
                edges.add(item)
                verts.add(item.verts[0])
                verts.add(item.verts[1])

        grouped_edges: List[Set[BMEdge]] = []
        visited_verts: Set[BMVert] = set()
        for v in verts:
            if v not in visited_verts:
                group: Set[BMEdge] = set()
                JVBuilderBase._get_connected_edges(
                    v, verts, visited_verts, edges, group
                )
                grouped_edges.append(group)

        for group in grouped_edges:
            bmesh.ops.edgenet_fill(mesh, edges=list(group))

    @staticmethod
    def _get_connected_edges(
        v: BMVert,
        all_vs: Set[BMVert],
        visited_vs: Set[BMVert],
        edges: Union[dict, Set[BMEdge]],
        g: Set[BMEdge],
    ):
        """Starting at a given vertex 'v', follow all attached edges that are in 'edges'
        and collect them together into 'g'. The following aspect is recursive, and the
        end result will be all connected edges being put in 'g'.

        :param v: The vertex to follow
        :param all_vs: A set of all the vertices from the newly created geometry
        :param visited_vs: The vertices that we have visited so far
        :param edges: A set/dict of all the edges from the newly created geometry
        :param g: The set of edges we are building that are connected
        """
        visited_vs.add(v)

        for edge in v.link_edges:
            if edge in edges:
                g.add(edge)

                for vert in edge.verts:
                    if (
                        vert in all_vs and vert not in visited_vs
                    ):  # if we have a vertex we haven't visited yet
                        JVBuilderBase._get_connected_edges(
                            vert, all_vs, visited_vs, edges, g
                        )

    @staticmethod
    def _group_connected_faces(faces: Set[BMFace]) -> List[Set[BMFace]]:
        """Take a set of faces and group them together based on whether
        the faces are connected, aka, share an edge

        :param faces: A set of faces
        :return: A list of sets of grouped faces
        """
        groups: List[Set[BMFace]] = []
        visited: Set[BMFace] = set()
        for face in faces:
            if face not in visited:
                group: Set[BMFace] = set()
                JVBuilderBase._group_connected_faces_worker(face, faces, visited, group)
                groups.append(group)

        return groups

    @staticmethod
    def _group_connected_faces_worker(
        face: BMFace,
        all_faces: Set[BMFace],
        visited_faces: Set[BMFace],
        group: Set[BMFace],
    ):
        group.add(face)
        visited_faces.add(face)
        for edge in face.edges:
            for linked_face in edge.link_faces:
                if linked_face in all_faces and linked_face not in visited_faces:
                    JVBuilderBase._group_connected_faces_worker(
                        linked_face, all_faces, visited_faces, group
                    )

    @staticmethod
    def _rotate_mesh_vertices(mesh: BMesh, rotation: Euler):
        for vert in mesh.verts:
            vert.co.rotate(rotation)

        mesh.verts.ensure_lookup_table()

    @staticmethod
    def _transform_vertex_positions(
        vertices,
        rotation=Euler(),
        before_translation=Vector(),
        after_translation=Vector(),
    ):
        for i in range(len(vertices)):
            c = Vector(vertices[i])
            c += before_translation
            c.rotate(rotation)
            c += after_translation
            vertices[i] = tuple(c)

    @staticmethod
    def _add_material_index(faces: Iterable[BMFace], index: int):
        for f in faces:
            f.material_index = index

    @staticmethod
    def _add_uv_seams_for_solidified_plane(
        extruded_geometry: Geometry,
        original_edges: List[BMEdge],
        mesh,
    ):
        """Add seams to all vertical edges and n-1 of the n top edges to allow the
        mesh to be unwrapped and lay flat. To determine which top edges should be
        marked, first, all new vertices are collected, and then the edges connecting
        them are grouped together based on whether they are connected or not. This
        groups new edges by board, tile, etc. Next, the number of new faces connected
        to each edge is used to determine which edges to mark. Only edges connected to
        one new face will be marked. Then mark all vertical edges.

        :param extruded_geometry: The new vertices, edges, and faces from
            bmesh.ops.solidify["geom"]
        :param original_edges: The edges that formed the original plane
        :param mesh: the current mesh object
        """
        new_edges: Dict[BMEdge, int] = (
            {}
        )  # new edge -> count of new faces that share it
        new_faces: Set[BMFace] = set()
        new_vertices: Set[BMVert] = set()
        for item in extruded_geometry:
            if isinstance(item, BMEdge):
                new_edges[item] = 0
            elif isinstance(item, BMVert):
                new_vertices.add(item)
            else:
                new_faces.add(item)

        # determine how many new faces are connected to each edge
        for face in new_faces:
            for edge in face.edges:
                new_edges[edge] += 1

        # group edges by whether they are connected or not
        visited_vertices: Set[BMVert] = set()
        grouped_edges: List[Set[BMEdge]] = []
        for v in new_vertices:
            if v not in visited_vertices:
                group: Set[BMEdge] = set()
                JVBuilderBase._get_connected_edges(
                    v, new_vertices, visited_vertices, new_edges, group
                )
                grouped_edges.append(group)

        # mark top edges
        for group in grouped_edges:
            first = True
            for edge in group:
                if new_edges[edge] == 1 and first:  # skip one edge
                    first = False
                    continue
                elif new_edges[edge] == 1:
                    edge.seam = True

        # mark vertical edges
        og_edges = set(original_edges)
        for edge in mesh.edges:
            if edge not in og_edges and edge not in new_edges:
                edge.seam = True

    @staticmethod
    def _cutouts(mesh: BMesh, props: JVProperties, object_matrix: Matrix):
        """For each added cutout, bisect the mesh according to the 6 faces
        of the cutout cubes. Then manually remove all faces from the mesh
        that are contained within the cutout cubes.

        :param mesh: The bmesh mesh
        :param props: All JV properties
        :param object_matrix: The matrix of the base object, needed for
            non-local cutouts
        """
        mesh.normal_update()
        inv_matrix = object_matrix.inverted()
        _, inv_rot, _ = inv_matrix.decompose()

        for cutout in props.cutouts:
            hx, hy, hz = Vector(cutout.dimensions) / 2
            center_normals = (
                ((hx, 0, 0), (-1, 0, 0)),
                ((-hx, 0, 0), (1, 0, 0)),
                ((0, +hy, 0), (0, -1, 0)),
                ((0, -hy, 0), (0, 1, 0)),
                ((0, 0, +hz), (0, 0, -1)),
                ((0, 0, -hz), (0, 0, 1)),
            )

            # transform plane centers and normals
            center_offset = Vector((hx, hy, hz))
            planes: List[Tuple[VecTuple, VecTuple]] = []
            for c, n in center_normals:
                p_center, p_normal = Vector(c), Vector(n)

                p_center.rotate(cutout.rotation)
                p_normal.rotate(cutout.rotation)
                p_center += cutout.location + center_offset

                if not cutout.local:
                    p_center: Vector = inv_matrix @ p_center
                    p_normal.rotate(inv_rot)

                planes.append((tuple(p_center), tuple(p_normal)))

            for plane_co, plane_normal in planes:
                bmesh.ops.bisect_plane(
                    mesh,
                    geom=[*mesh.faces, *mesh.edges, *mesh.verts],
                    dist=0.001,
                    plane_co=plane_co,
                    plane_no=plane_normal,
                )

                mesh.verts.ensure_lookup_table()
                mesh.edges.ensure_lookup_table()
                mesh.faces.ensure_lookup_table()

            # determine corner locations to know what geometry to remove
            corners: List[Vector] = []
            for lz in (-hz, hz):
                for ly in (-hy, hy):
                    for lx in (-hx, hx):
                        corners.append(Vector((lx, ly, lz)))

            # transform cutout corners
            for i in range(len(corners)):
                corners[i].rotate(cutout.rotation)
                corners[i] += cutout.location

                if not cutout.local:
                    corners[i] = inv_matrix @ corners[i]

            # find min and maxes of the corners to know the cutouts bounds
            mins, maxs = list(corners[0]), list(corners[0])
            for corner in corners:
                for i in range(3):
                    mins[i] = min(mins[i], corner[i])
                    maxs[i] = max(maxs[i], corner[i])

            cuboid = CuboidalRegion(planes)

            # remove faces
            to_remove = []
            for face in mesh.faces:
                c = face.calc_center_median()
                if c in cuboid:
                    to_remove.append(face)

            for face in to_remove:
                mesh.faces.remove(face)

            JVBuilderBase._clean_mesh(mesh)

    @staticmethod
    def _clean_mesh(mesh: BMesh):
        """Remove all vertices and edges that aren't connected to anything"""
        to_remove = []
        for edge in mesh.edges:
            if edge.is_wire:
                to_remove.append(edge)

        for edge in to_remove:
            mesh.edges.remove(edge)

        to_remove.clear()
        for vertex in mesh.verts:
            if vertex.is_wire:
                to_remove.append(vertex)

        for vertex in to_remove:
            mesh.verts.remove(vertex)

        mesh.verts.ensure_lookup_table()
        mesh.edges.ensure_lookup_table()
        mesh.faces.ensure_lookup_table()

    @classmethod
    def _generate_mesh_from_converted_object(
        cls,
        props: JVProperties,
        context: Context,
        rot_offset=(0, 0, 0),
        geometry_func_name="_geometry",
    ) -> BMesh:
        """Since the object is converted, go through each face group, creating
        a new mesh, cutting it, and then joining them all together into a mesh
        which is returned.

        :param cls: The architecture class to use for generating the geometry
        :param props: JVProperties
        :param context: The current context
        :param rot_offset: A rotation offset for use with siding as it is built
            vertically not horizontally
        :param geometry_func_name: The name of the method on the class that
            generates the geometry. The method must be take in props and
            dimensions and return verts and faces
        """
        objects: List[Object] = []
        main_obj = context.object
        src = props.convert_source_object

        for fg in src.jv_properties.face_groups:  # face groups on original object
            verts, faces = getattr(cls, geometry_func_name)(props, tuple(fg.dimensions))
            rotated_verts: List[VecTuple] = []

            # rotate and shift vertices
            rot = Euler([fg.rotation[i] + rot_offset[i] for i in range(3)])
            for v in verts:
                vv = Vector(v)
                vv.rotate(rot)
                vv += fg.location
                rotated_verts.append(tuple(vv))

            mesh = bmesh.new()
            cls._build_mesh_from_geometry(mesh, rotated_verts, faces)

            bpy.ops.mesh.primitive_cube_add()
            new_obj = context.object
            new_obj.location = src.location
            objects.append(new_obj)
            mesh.to_mesh(new_obj.data)

            if fg.is_convex:
                mesh.normal_update()

                # cut mesh using bisect_plane for every edge, remove all geometry outside of planes
                planes = []
                for plane in fg.bisecting_planes:
                    planes.append((tuple(plane.center), tuple(plane.normal)))

                cls._cut_meshes([mesh], planes)
                mesh.to_mesh(new_obj.data)
            else:
                bpy.ops.object.modifier_add(type="BOOLEAN")
                new_obj.modifiers["Boolean"].object = fg.boolean_object
                new_obj.modifiers["Boolean"].operation = 'INTERSECT'
                bpy.ops.object.modifier_apply(modifier="Boolean")

            mesh.free()

        # join objects
        for obj in context.selected_objects:
            obj.select_set(False)
        for obj in objects:
            obj.select_set(True)
        context.view_layer.objects.active = objects[0]

        if len(objects) > 1:
            bpy.ops.object.join()

        bm = bmesh.new()
        bm.from_mesh(context.object.data)
        cls._clean_mesh(bm)

        bpy.ops.object.delete()  # remove object formed from joining meshes

        main_obj.select_set(True)
        context.view_layer.objects.active = main_obj

        return bm

    @staticmethod
    def _slope_top(props: JVProperties, meshes: List[BMesh]):
        # clock-wise is positive for angles in mathutils
        center = Vector((props.length / 2, 0, props.height))
        center += props.pitch_offset
        angle = atan(props.pitch / 12)  # angle of depression

        right_normal = Vector((1, 0, 0))
        right_normal.rotate(Euler((0, angle + radians(90), 0)))
        left_normal = Vector((1, 0, 0))
        left_normal.rotate(Euler((0, radians(90) - angle, 0)))

        JVBuilderBase._cut_meshes(
            meshes, [(center, left_normal), (center, right_normal)]
        )

    @staticmethod
    def _mortar_geometry(props: JVProperties, dims: Tuple[float, float]):
        # account for jointing
        upper_x, upper_z = dims
        th = props.thickness_thick * (1 - (props.grout_depth / 100)) + props.gap_uniform
        lx = th if props.joint_left else 0
        rx = th if props.joint_right else 0

        verts = [
            (-lx, 0, 0),
            (upper_x + rx, 0, 0),
            (upper_x + rx, 0, upper_z),
            (-lx, 0, upper_z),
        ]
        faces = [(0, 3, 2, 1)]

        return verts, faces

    @staticmethod
    def _mirror(mesh: BMesh, axis: Literal["X", "Y", "Z"] = "X"):
        """Duplicate and mirror existing geometry across the specified axis"""
        # duplicate geometry
        new_geom: Geometry = bmesh.ops.duplicate(
            mesh, geom=[*mesh.verts, *mesh.edges, *mesh.faces]
        )["geom"]

        i = {"X": 1, "Y": 0, "Z": 2}[axis.upper()]
        for item in new_geom:
            if isinstance(item, BMVert):
                item.co[i] *= -1

        mesh.verts.ensure_lookup_table()
        mesh.faces.ensure_lookup_table()
