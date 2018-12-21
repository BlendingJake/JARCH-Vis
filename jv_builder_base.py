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

    @staticmethod
    def _create_quad(verts: list, faces: list, x: float, y: float, width: float, length: float, upper_x: float,
                     upper_y: float):
        """
        Create a new quad between [x, x+width] and [y, y+length], cut to start within upper bounds
        :param verts: the list of verts
        :param faces: the list of faces
        :param x: the starting x value
        :param y: the starting y value
        :param width: the width of the quad
        :param length: the length of the quad
        :param upper_x: the max x value
        :param upper_y: the max y value
        """
        width = min(width, upper_x-x)
        length = min(length, upper_y-y)

        verts += [
            (x, y, 0),
            (x+width, y, 0),
            (x+width, y+length, 0),
            (x, y+length, 0)
        ]

        p = len(verts) - 4
        faces.append((p, p+1, p+2, p+3))

        return verts, faces
