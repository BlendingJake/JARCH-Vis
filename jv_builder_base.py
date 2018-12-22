import bpy
import bmesh
from random import uniform


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
    def _solidfy(mesh, direction_vector, thickness_func, thickness_per_vert=False):
        modified = set()
        for item in bmesh.ops.solidify(mesh, geom=mesh.faces[:], thickness=0)["geom"]:
            if isinstance(item, bmesh.types.BMFace):
                th = thickness_func()

                for v in item.verts:
                    if v not in modified:
                        if thickness_per_vert:  # if thickness is determined per vertex, then get a new thickness value
                            th = thickness_func()

                        v.co.x += direction_vector[0] * th
                        v.co.y += direction_vector[1] * th
                        v.co.z += direction_vector[2] * th

                        modified.add(v)

    @staticmethod
    def _create_variance_function(vary: bool, base_amount: float, variance: float):
        variance /= 100  # convert to decimal

        if vary:
            return lambda: uniform(base_amount * (1 - variance), base_amount * (1 + variance))
        else:
            return lambda: base_amount

    @staticmethod
    def _cut_mesh(mesh, planes: list):
        """
        Take the bmesh object and bisect it with all the planes given and remove the geometry outside of the planes
        :param mesh: the mesh to operate on
        :param planes: a list of tuples, each tuple being (plane position, plane normal). The normals should point
                        towards the center of the mesh, aka, geometry on the opposite side of the normal will be removed
        """
        for plane in planes:
            pos, normal = plane
            bmesh.ops.bisect_plane(mesh, geom=mesh.faces[:] + mesh.edges[:] + mesh.verts[:], dist=0.001, plane_co=pos,
                                   plane_no=normal, clear_inner=True)
