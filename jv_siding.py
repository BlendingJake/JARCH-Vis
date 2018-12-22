from . jv_builder_base import JVBuilderBase
from . jv_utils import Units
from mathutils import Vector, Euler
from math import atan, radians


class JVSiding(JVBuilderBase):
    @staticmethod
    def draw(props, layout):
        layout.prop(props, "siding_pattern", icon="MOD_TRIANGULATE")

        layout.separator()
        row = layout.row()
        row.prop(props, "height")
        row.prop(props, "length")

        if props.siding_pattern in ("regular", "tongue_groove"):
            layout.separator()
            row = layout.row()
            row.prop(props, "board_width_medium")
            row.prop(props, "board_length_long")

        if props.siding_pattern in ("regular", "tongue_groove"):
            layout.separator()
            layout.prop(props, "siding_direction", icon="ORIENTATION_VIEW")

        # length and width variance
        if props.siding_pattern in ("regular", "tongue_groove"):
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_width", icon="RNDCURVE")
            if props.vary_width:
                row.prop(props, "width_variance")

            layout.separator()
            row = layout.row()

            row.prop(props, "vary_length", icon="RNDCURVE")
            if props.vary_length:
                row.prop(props, "length_variance")

        # thickness and variance
        layout.separator()
        layout.prop(props, "thickness")

        row = layout.row()
        row.prop(props, "vary_thickness", icon="RNDCURVE")
        if props.vary_thickness:
            row.prop(props, "thickness_variance")

        # slope
        layout.separator()
        row = layout.row()
        row.prop(props, "slope_top", icon="LINCURVE")
        if props.slope_top:
            row.prop(props, "pitch")
            layout.prop(props, "pitch_offset")

    @staticmethod
    def update(props, context):
        mesh = JVSiding._start(context)
        verts, faces = JVSiding._geometry(props)

        mesh.clear()
        for v in verts:
            mesh.verts.new(v)
        mesh.verts.ensure_lookup_table()

        for f in faces:
            mesh.faces.new([mesh.verts[i] for i in f])
        mesh.faces.ensure_lookup_table()

        # cut slope
        if props.slope_top:
            # clock-wise is positive for angles in mathutils
            center = Vector((props.length / 2, 0, props.height))
            center += props.pitch_offset
            angle = atan(props.pitch / 12)  # angle of depression

            right_normal = Vector((1, 0, 0))
            right_normal.rotate(Euler((0, angle+radians(90), 0)))
            left_normal = Vector((1, 0, 0))
            left_normal.rotate(Euler((0, radians(90) - angle, 0)))

            JVSiding._cut_mesh(mesh, [
                (center, left_normal),
                (center, right_normal)
            ])

            mesh.faces.ensure_lookup_table()
            mesh.edges.ensure_lookup_table()
            mesh.verts.ensure_lookup_table()

        # solidify
        if props.siding_pattern != "tongue_groove":
            JVSiding._solidfy(mesh, (0, -1, 0), JVSiding._create_variance_function(props.vary_thickness,
                                                                                   props.thickness,
                                                                                   props.thickness_variance))

        JVSiding._finish(context, mesh)

    @staticmethod
    def _geometry(props):
        verts, faces = [], []

        # dynamically call correct method as their names will match up with the style name
        getattr(JVSiding, "_{}".format(props.flooring_pattern))(props, verts, faces)

        return verts, faces

    @staticmethod
    def _regular(props, verts, faces):
        length, width, gap = props.board_length_long, props.board_width_medium, props.gap_uniform

        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        upper_x, upper_z = props.length, props.height

        if props.siding_direction == "vertical":
            x = 0
            while x < upper_x:
                z = 0

                cur_width = width_variance()
                while z < upper_z:
                    cur_length = length_variance()

                    trimmed_width = min(cur_width, upper_x-x)
                    trimmed_length = min(cur_length, upper_z-z)

                    verts += [
                        (x, 0, z),
                        (x+trimmed_width, 0, z),
                        (x+trimmed_width, 0, z+trimmed_length),
                        (x, 0, z+trimmed_length)
                    ]

                    p = len(verts) - 4
                    faces.append((p, p+1, p+2, p+3))

                    z += cur_length + gap
                x += cur_width + gap
        else:
            z = 0
            while z < upper_z:
                x = 0

                cur_width = width_variance()
                while x < upper_x:
                    cur_length = length_variance()

                    trimmed_width = min(cur_width, upper_z - z)
                    trimmed_length = min(cur_length, upper_x - x)

                    verts += [
                        (x, 0, z),
                        (x + trimmed_length, 0, z),
                        (x + trimmed_length, 0, z+trimmed_width),
                        (x, 0, z+trimmed_width)
                    ]

                    p = len(verts) - 4
                    faces.append((p, p + 1, p + 2, p + 3))

                    x += cur_length + gap
                z += cur_width + gap

    @staticmethod
    def _tongue_groove(props, verts, faces):
        """
        Will be faux tongue & groove meaning it will look right from the front-face, but not be
        a fully closed mesh
        """
        length, width, gap, th = props.board_length_long, props.board_width_medium, props.gap_uniform, props.thickness

        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        upper_x, upper_z = props.length, props.height

        hi = Units.H_INCH

        if props.siding_direction == "vertical":
            x = 0
            while x < upper_x:
                z = 0

                width = width_variance()
                while z < upper_z:
                    length = length_variance()

                    for zz in (z, z+length):  # bottom and top groups of vertices
                        print("here")
                        verts += [
                            (x, 0, zz),
                            (x+hi+gap, 0, zz),
                            (x+hi+gap, -th, zz),
                            (x+hi+width+gap, -th, zz),
                            (x+hi+width+gap, -th+hi, zz),
                            (x+width+gap, -th+hi, zz)
                        ]

                    p = len(verts) - 12
                    for i in range(5):
                        faces.append((p+i, p+i+1, p+i+7, p+i+6))

                    z += length + gap
                x += width + gap
        else:
            z = 0
            # while z < upper_z:
            #     x = 0
            #
            #     width = width_variance()
            #     while x < upper_x:
            #         length = length_variance()
            #
            #         trimmed_width = min(cur_width, upper_z - z)
            #         trimmed_length = min(cur_length, upper_x - x)
            #
            #         verts += [
            #             (x, 0, z),
            #             (x + trimmed_length, 0, z),
            #             (x + trimmed_length, 0, z+trimmed_width),
            #             (x, 0, z+trimmed_width)
            #         ]
            #
            #         p = len(verts) - 4
            #         faces.append((p, p + 1, p + 2, p + 3))
            #
            #         x += cur_length + gap
            #     z += cur_width + gap
