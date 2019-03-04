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
from random import uniform
from mathutils import Vector, Euler
from typing import Union, List
from math import radians, atan
from . jv_utils import CuboidalRegion


class JVBuilderBase:
    is_cutable = False
    is_convertible = False

    @staticmethod
    def draw(props, layout):
        pass

    @staticmethod
    def update(props, context):
        pass

    @staticmethod
    def delete(props, context):
        src = props.convert_source_object

        if src is not None:  # remove boolean objects if non-convex face groups
            for fg in src.jv_properties.face_groups:
                if not fg.is_convex:
                    fg.boolean_object.hide_viewport = False
                    fg.boolean_object.select_set(True)

        bpy.ops.object.delete()

        if src is not None:
            src.hide_viewport = False
            src.select_set(True)
            context.view_layer.objects.active = src

    @staticmethod
    def _start(context):
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
    def _finish(context, bm: bmesh.types.BMesh):
        bm.normal_update()
        bm.to_mesh(context.object.data)
        bm.free()

    @staticmethod
    def _geometry(props, dims: tuple):
        return [], []

    @staticmethod
    def _build_mesh_from_geometry(mesh: bmesh.types.BMesh, vertices: list, faces: list):
        """
        Take a bmesh mesh, vertices positions, and face-vertex indices and clear and add the vertices and faces
        to the mesh object
        :param mesh: the bmesh object to clear and add the geometry to
        :param vertices: tuples of the positions of the vertices
        :param faces: tuples of the indices of the vertices that make up the face
        """
        mesh.clear()
        for v in vertices:
            mesh.verts.new(v)
        mesh.verts.ensure_lookup_table()

        for f in faces:
            mesh.faces.new([mesh.verts[i] for i in f])
        mesh.faces.ensure_lookup_table()

    @staticmethod
    def _solidify(mesh: bmesh.types.BMesh, thickness: Union[callable, float]):
        """
        Solidify the mesh. If 'thickness' is callable, then use the normal as the direction
        :param mesh: the mesh to solidify
        :param thickness: If thickness is callable, then each new face gets a thickness value from the function.
                Otherwise, the value will be used consistently.
        :return:
        """
        mesh.normal_update()
        visited = set()
        start_th = 0 if callable(thickness) else thickness

        new_geom = bmesh.ops.solidify(mesh, geom=mesh.faces[:], thickness=start_th)["geom"]

        # manually add thickness if 'thickness' is callable
        if callable(thickness):
            faces = set()
            for item in new_geom:
                if isinstance(item, bmesh.types.BMFace):
                    faces.add(item)

            groups = JVBuilderBase._group_connected_faces(faces)
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

        if vary:
            return lambda: uniform(base_amount * (1 - variance), base_amount * (1 + variance))
        else:
            return lambda: base_amount

    @staticmethod
    def _cut_meshes(meshes: list, planes: list, fill_holes=False, remove_geom=True):
        """
        Take the bmesh object and bisect it with all the planes given and remove the geometry outside of the planes
        :param meshes: a list of the meshes to cut
        :param planes: a list of tuples, each tuple being (plane position, plane normal). The normals should point
                        towards the center of the mesh, aka, geometry on the opposite side of the normal will be removed
        """
        for mesh in meshes:
            for plane in planes:
                pos, normal = plane
                geom = bmesh.ops.bisect_plane(mesh, geom=mesh.faces[:] + mesh.edges[:] + mesh.verts[:], dist=0.001,
                                              plane_co=pos, plane_no=normal, clear_inner=remove_geom)

                if fill_holes:
                    JVBuilderBase._fill_holes(mesh, geom["geom_cut"])

            mesh.faces.ensure_lookup_table()
            mesh.edges.ensure_lookup_table()
            mesh.verts.ensure_lookup_table()

    @staticmethod
    def _fill_holes(mesh: bmesh.types.BMesh, cut_geometry):
        """
        Given a mesh and geometry generated by using bisect_plane, fill the holes/ends
        :param mesh: the mesh to operate
        :param cut_geometry: a list of the new vertices, edges, and faces created by bisecting the mesh
        """
        verts, edges = set(), set()
        for item in cut_geometry:
            if isinstance(item, bmesh.types.BMEdge):
                edges.add(item)
                verts.add(item.verts[0])
                verts.add(item.verts[1])

        visited_verts = set()
        grouped_edges = []

        for v in verts:
            if v not in visited_verts:
                group = set()
                JVBuilderBase._get_connected_edges(v, verts, visited_verts, edges, group)
                grouped_edges.append(group)

        for group in grouped_edges:
            bmesh.ops.edgenet_fill(mesh, edges=list(group))

    @staticmethod
    def _get_connected_edges(v, all_vs: set, visited_vs: set, edges: Union[dict, set], g: set):
        """
        Starting at a given vertex 'v', follow all attached edges that are in 'edges' and collect them together into 'g'
        The follow aspect is recursive, and the end result will be all connected edges being put in 'g'
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
                    if vert in all_vs and vert not in visited_vs:  # if we have a vertex we haven't visited yet
                        JVBuilderBase._get_connected_edges(vert, all_vs, visited_vs, edges, g)

    @staticmethod
    def _group_connected_faces(faces: set) -> List[set]:
        """
        Take a set of faces and group them together based on whether the faces are connected, aka, share an edge
        :param faces: a set of faces
        :return: a list of sets of grouped faces
        """
        groups = []
        visited = set()
        for face in faces:
            if face not in visited:
                group = set()
                JVBuilderBase._group_connected_faces_worker(face, faces, visited, group)
                groups.append(group)

        return groups

    @staticmethod
    def _group_connected_faces_worker(face: bmesh.types.BMFace, all_faces, visited_faces, group):
        group.add(face)
        visited_faces.add(face)
        for edge in face.edges:
            for linked_face in edge.link_faces:
                if linked_face in all_faces and linked_face not in visited_faces:
                    JVBuilderBase._group_connected_faces_worker(linked_face, all_faces, visited_faces, group)

    @staticmethod
    def _rotate_mesh_vertices(mesh, rotation):
        for vert in mesh.verts:
            vert.co.rotate(rotation)

        mesh.verts.ensure_lookup_table()

    @staticmethod
    def _transform_vertex_positions(vertices, rotation=Euler((0, 0, 0)), before_translation=Vector((0, 0, 0)),
                                    after_translation=Vector((0, 0, 0))):
        for i in range(len(vertices)):
            c = Vector(vertices[i])
            c += before_translation
            c.rotate(rotation)
            c += after_translation
            vertices[i] = tuple(c)

    @staticmethod
    def _add_material_index(faces, index: int):
        for f in faces:
            f.material_index = index

    @staticmethod
    def _add_uv_seams_for_solidified_plane(extruded_geometry, original_edges, mesh):
        """
        Add seams to all vertical edges and n-1 of the n top edges to allow the mesh to be unwrapped and lay flat.
        To determine which top edges should be marked, first, all new vertices are collected, and then the edges
        connecting them are grouped together based on whether they are connected or not. This groups new edges by
        board, tile, etc. Next, the number of new faces connected to each edge is used to determine which edges to mark.
        Only edges connected to one new face will be marked. Then mark all vertical edges
        :param extruded_geometry: The new vertices, edges, and faces from bmesh.ops.solidify["geom"]
        :param original_edges: the edges that formed the original plane
        :param mesh: the current mesh object
        """
        new_vertices = set()
        new_faces = set()
        new_edges = {}  # maps new edge -> count of new faces that share it
        for item in extruded_geometry:
            if isinstance(item, bmesh.types.BMEdge):
                new_edges[item] = 0
            elif isinstance(item, bmesh.types.BMVert):
                new_vertices.add(item)
            else:
                new_faces.add(item)

        # determine how many new faces are connected to each edge
        for face in new_faces:
            for edge in face.edges:
                new_edges[edge] += 1

        # group edges by whether they are connected or not
        visited_vertices = set()
        grouped_edges = []
        for v in new_vertices:
            if v not in visited_vertices:
                group = set()
                JVBuilderBase._get_connected_edges(v, new_vertices, visited_vertices, new_edges, group)
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
    def _cutouts(mesh: bmesh.types.BMesh, props, object_matrix):
        """
        For each added cutout, bisect the mesh according to the 6 faces of the cutout cubes. Then manually
        remove all faces from the mesh that are contained within the cutout cubes.
        :param mesh: the bmesh mesh
        :param props: all JV properties
        :param object_matrix: the matrix of the base object, needed for non-local cutouts
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
                ((0, 0, -hz), (0, 0, 1))
            )

            # transform plane centers and normals
            center_offset = Vector((hx, hy, hz))
            planes = []
            for c, n in center_normals:
                p_center, p_normal = Vector(c), Vector(n)

                p_center.rotate(cutout.rotation)
                p_normal.rotate(cutout.rotation)
                p_center += cutout.location + center_offset

                if not cutout.local:
                    p_center = inv_matrix @ p_center  # using new infix matrix multiplication
                    p_normal.rotate(inv_rot)

                planes.append((tuple(p_center), tuple(p_normal)))

            for plane_co, plane_normal in planes:
                bmesh.ops.bisect_plane(mesh, geom=mesh.faces[:] + mesh.edges[:] + mesh.verts[:], dist=0.001,
                                       plane_co=plane_co, plane_no=plane_normal)

                mesh.verts.ensure_lookup_table()
                mesh.edges.ensure_lookup_table()
                mesh.faces.ensure_lookup_table()

            # determine corner locations to know what geometry to remove
            corners = []
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
    def _clean_mesh(mesh: bmesh.types.BMesh):
        """
        Remove all vertices and edges that aren't connected to anything
        :param mesh: the mesh to clean
        """
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
    def _generate_mesh_from_converted_object(cls, props, context, rot_offset=(0, 0, 0), geometry_func_name="_geometry"):
        """
        Since the object is converted, go through each face group, creating a new mesh, cutting it,
        and then joining them all together into a mesh which is returned
        :param cls: the architecture class to use for generating the geometry
        :param props: JVProperties
        :param context: the current context
        :param rot_offset: a rotation offset for use with siding as it is built vertically not horizontally
        :param geometry_func_name: the name of the method on the class that generates the geometry. The method
            must be take in props and dimensions and return verts and faces
        :return: the completed mesh
        """
        objects = []
        main_obj = context.object
        src = props.convert_source_object

        for fg in src.jv_properties.face_groups:  # face groups on original object
            verts, faces = getattr(cls, geometry_func_name)(props, tuple(fg.dimensions))
            rotated_verts = []

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
                bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

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
    def _slope_top(props, meshes):
        # clock-wise is positive for angles in mathutils
        center = Vector((props.length / 2, 0, props.height))
        center += props.pitch_offset
        angle = atan(props.pitch / 12)  # angle of depression

        right_normal = Vector((1, 0, 0))
        right_normal.rotate(Euler((0, angle + radians(90), 0)))
        left_normal = Vector((1, 0, 0))
        left_normal.rotate(Euler((0, radians(90) - angle, 0)))

        JVBuilderBase._cut_meshes(meshes, [
            (center, left_normal),
            (center, right_normal)
        ])

    @staticmethod
    def _mortar_geometry(props, dims: tuple):
        # account for jointing
        upper_x, upper_z = dims
        th = props.thickness_thick * (1 - (props.grout_depth / 100)) + props.gap_uniform
        lx = th if props.joint_left else 0
        rx = th if props.joint_right else 0

        verts = [(-lx, 0, 0), (upper_x + rx, 0, 0), (upper_x + rx, 0, upper_z), (-lx, 0, upper_z)]
        faces = [(0, 3, 2, 1)]

        return verts, faces

    @staticmethod
    def _mirror(mesh, axis='X'):
        """
        Duplicate and mirror existing geometry across the specified axis
        :param mesh: the mesh to duplicate and mirror
        :param axis: the axis to mirror across, must be in {'X', 'Y', 'Z'}
        :return:
        """
        # duplicate geometry
        new_geom = bmesh.ops.duplicate(mesh, geom=mesh.verts[:] + mesh.edges[:] + mesh.faces[:])["geom"]

        i = {'X': 1, 'Y': 0, 'Z': 2}[axis.upper()]
        for item in new_geom:
            if isinstance(item, bmesh.types.BMVert):
                item.co[i] *= -1

        mesh.verts.ensure_lookup_table()
        mesh.faces.ensure_lookup_table()
