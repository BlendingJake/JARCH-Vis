import bpy
import bmesh
from random import uniform
from mathutils import Vector


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
        bpy.ops.object.mode_set(mode='EDIT')

        bm = bmesh.from_edit_mesh(context.object.data)
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        return bm

    @staticmethod
    def _finish(context, mesh):
        mesh.normal_update()
        bmesh.update_edit_mesh(context.object.data, True)

        bpy.ops.object.mode_set(mode='OBJECT')
        mesh.free()

    @staticmethod
    def _geometry(props):
        pass

    @staticmethod
    def _solidify(mesh, thickness_func, direction_vector=None):
        visited = set()
        for item in bmesh.ops.solidify(mesh, geom=mesh.faces[:], thickness=0)["geom"]:
            if isinstance(item, bmesh.types.BMFace):
                th = thickness_func()

                if direction_vector is None:
                    dv = item.normal
                else:
                    dv = direction_vector

                for v in item.verts:
                    if v not in visited:
                        v.co.x += dv[0] * th
                        v.co.y += dv[1] * th
                        v.co.z += dv[2] * th

                        visited.add(v)

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
    def _fill_holes(mesh, cut_geometry):
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
                JVBuilderBase._get_connected(v, verts, visited_verts, edges, group)
                grouped_edges.append(group)

        for group in grouped_edges:
            bmesh.ops.edgenet_fill(mesh, edges=list(group))

    @staticmethod
    def _get_connected(v, all_vs: set, visited_vs: set, edges: set, g: set):
        """
        Recursive follow the edges that are connected to v if the edges are part of the newly created geometry
        :param v: The vertex to follow
        :param all_vs: A set of all the vertices from the newly created geometry
        :param visited_vs: The vertices that we have visited so far
        :param edges: A set of all the edges from the newly created geometry
        :param g: The set of edges we are building that are connected
        """
        visited_vs.add(v)

        for edge in v.link_edges:
            if edge in edges:
                g.add(edge)

                for vert in edge.verts:
                    if vert in all_vs and vert not in visited_vs:  # if we have a vertex we haven't visited yet
                        JVBuilderBase._get_connected(vert, all_vs, visited_vs, edges, g)

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
