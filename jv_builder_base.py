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
        pass

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
    def _solidfy(mesh, direction_vector, thickness_func):
        for item in bmesh.ops.solidify(mesh, geom=mesh.faces[:], thickness=0)["geom"]:
            if isinstance(item, bmesh.types.BMFace):
                th = thickness_func()

                for v in item.verts:
                    v.co.x += direction_vector[0] * th
                    v.co.y += direction_vector[1] * th
                    v.co.z += direction_vector[2] * th

    @staticmethod
    def _create_variance_function(vary: bool, base_amount: float, variance: float):
        variance /= 100  # convert to decimal

        if vary:
            return lambda: uniform(base_amount * (1 - variance), base_amount * (1 + variance))
        else:
            return lambda: base_amount
