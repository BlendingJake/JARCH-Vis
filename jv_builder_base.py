import bpy
import bmesh
from random import uniform
from mathutils import Vector
from typing import Union, List


class JVBuilderBase:
    @staticmethod
    def draw(props, layout):
        pass

    @staticmethod
    def update(props, context):
        pass

    @staticmethod
    def delete(props, context):
        bpy.ops.object.delete()

    @staticmethod
    def _start(context):
        # bpy.ops.object.mode_set(mode='EDIT')

        # bm = bmesh.from_edit_mesh(context.object.data)
        bm = bmesh.new()
        bm.from_mesh(context.object.data)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        return bm

    @staticmethod
    def _finish(context, bm: bmesh.types.BMesh):
        bm.normal_update()
        # bmesh.update_edit_mesh(context.object.data, True)
        bm.to_mesh(context.object.data)

        # bpy.ops.object.mode_set(mode='OBJECT')
        bm.free()

    @staticmethod
    def _geometry(props, dims: tuple):
        pass

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
    def _cut_meshes(meshes: list, planes: list, fill_holes=False):
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
                                              plane_co=pos, plane_no=normal, clear_inner=True)

                if fill_holes:
                    JVBuilderBase._fill_holes(mesh, geom["geom_cut"])

            mesh.faces.ensure_lookup_table()
            mesh.edges.ensure_lookup_table()
            mesh.verts.ensure_lookup_table()

    @staticmethod
    def _fill_holes(mesh: bmesh.types.BMesh, cut_geometry):
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
        grouped = []
        visited = set()
        for face in faces:
            if face not in visited:
                group = {face}
                visited.add(face)
                for edge in face.edges:
                    for linked_face in edge.link_faces:
                        if linked_face in faces:
                            group.add(linked_face)
                            visited.add(linked_face)

                grouped.append(group)

        return grouped

    @staticmethod
    def _rotate_mesh_vertices(mesh, rotation, origin=Vector((0, 0, 0))):
        for vert in mesh.verts:
            pos = vert.co - origin
            pos.rotate(rotation)
            vert.co = pos

        mesh.verts.ensure_lookup_table()

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
    def _cutouts(mesh: bmesh.types.BMesh, props):
        """
        For each added cutout, bisect the mesh according to the 6 faces of the cutout cubes. Then manually
        remove all faces from the mesh that are contained within the cutout cubes.
        :param mesh: the bmesh mesh
        :param props: all JV properties
        """
        mesh.normal_update()

        for cutout in props.cutouts:
            x, y, z, dx, dy, dz = *cutout.offset, *cutout.dimensions
            planes = (  # plane center and normal
                ((x, 0, 0), (1, 0, 0)),
                ((x+dx, 0, 0), (-1, 0, 0)),
                ((0, y, 0), (0, 1, 0)),
                ((0, y+dy, 0), (0, -1, 0)),
                ((0, 0, z), (0, 0, 1)),
                ((0, 0, z+dz), (0, 0, -1))
            )

            for plane_co, plane_normal in planes:
                bmesh.ops.bisect_plane(mesh, geom=mesh.faces[:] + mesh.edges[:] + mesh.verts[:], dist=0.001, plane_co=plane_co, plane_no=plane_normal)

                mesh.verts.ensure_lookup_table()
                mesh.edges.ensure_lookup_table()
                mesh.faces.ensure_lookup_table()

            # remove faces
            to_remove = []
            for face in mesh.faces:
                c = face.calc_center_median()
                if x <= c.x <= x+dx and y <= c.y <= y+dy and z <= c.z <= z+dz:
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
