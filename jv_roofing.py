from . jv_builder_base import JVBuilderBase
from mathutils import Euler
from math import atan, cos
from . jv_utils import Units


class JVRoofing(JVBuilderBase):
    @staticmethod
    def draw(props, layout):
        layout.prop(props, "roofing_pattern", icon="MOD_TRIANGULATE")

        layout.separator()
        row = layout.row()
        row.prop(props, "width")
        row.prop(props, "length")
        layout.prop(props, "pitch")
        layout.separator()

        if props.roofing_pattern == "tin_standing_seam":
            layout.prop(props, "pan_width")

        # row offset
        if props.roofing_pattern == "shingles_3_tab":
            row = layout.row()

            row.prop(props, "vary_row_offset", icon="RNDCURVE")
            if props.vary_row_offset:
                row.prop(props, "row_offset_variance")
            else:
                row.prop(props, "row_offset")

    @staticmethod
    def update(props, context):
        mesh = JVRoofing._start(context)
        verts, faces = JVRoofing._geometry(props)

        mesh.clear()
        for v in verts:
            mesh.verts.new(v)
        mesh.verts.ensure_lookup_table()

        for f in faces:
            mesh.faces.new([mesh.verts[i] for i in f])
        mesh.faces.ensure_lookup_table()

        # overall dimension cutting - length
        if props.roofing_pattern in ("tin_regular", "tin_angular", "tin_standing_seam", "shingles_3_tab"):
            JVRoofing._cut_meshes([mesh], [
                ((props.length, 0, 0), (-1, 0, 0))
            ])
        # overall dimension cutting - width
        if props.roofing_pattern == "shingles_3_tab":
            JVRoofing._cut_meshes([mesh], [
                ((0, props.width / cos(atan(props.pitch / 12)), 0), (0, -1, 0))
            ])

        # rotate
        rot = atan(props.pitch / 12)
        rotation = Euler((rot, 0, 0))
        JVRoofing._rotate_mesh_vertices(mesh, rotation)

        # mirror

        # solidify
        if props.roofing_pattern == "shingles_3_tab":
            th = 5*Units.STH_INCH
            JVRoofing._solidify(mesh, JVRoofing._create_variance_function(False, th, 0))

        JVRoofing._finish(context, mesh)

    @staticmethod
    def _geometry(props):
        verts, faces = [], []

        getattr(JVRoofing, "_{}".format(props.roofing_pattern))(props, verts, faces)

        return verts, faces

    @staticmethod
    def _tin_regular(props, verts, faces):
        ridge_steps = (
            (0, 0),
            (Units.H_INCH, Units.TQ_INCH),
            (5 * Units.ETH_INCH, 7 * Units.ETH_INCH),
            (11 * Units.STH_INCH, Units.INCH),
            (17 * Units.STH_INCH, Units.INCH),
            (9 * Units.ETH_INCH, 7 * Units.ETH_INCH),
            (5 * Units.Q_INCH, 3 * Units.Q_INCH)
        )

        valley_steps = (
            (0, 0),
            (13 * Units.ETH_INCH, 0),
            (15 * Units.ETH_INCH, Units.ETH_INCH),
            (21 * Units.ETH_INCH, Units.ETH_INCH)
        )

        # diagonal distance to prep for rotation of vertices
        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))
        offset_between_valley_accents = 23 * Units.ETH_INCH
        for y in (0, upper_y):
            x = 0
            while x < upper_x + offset_between_valley_accents:
                for step in ridge_steps:
                    verts.append((x + step[0], y, step[1]))
                x += 7 * Units.Q_INCH

                for _ in range(2):
                    for step in valley_steps:
                        verts.append((x + step[0], y, step[1]))
                    x += offset_between_valley_accents

                verts.append((x, y, 0))  # finish valley ridge
                x += offset_between_valley_accents - Units.INCH

        # faces
        offset = len(verts) // 2
        for i in range(offset - 1):
            faces.append((i, i + 1, i + offset + 1, i + offset))

    @staticmethod
    def _tin_angular(props, verts, faces):
        pan = 3*Units.INCH
        ridge_steps = ((0, 0), (Units.H_INCH, 5*Units.Q_INCH), (3*Units.H_INCH, 5*Units.Q_INCH), (2*Units.INCH, 0))
        valley_steps = ((0, 0), (pan, 0), (pan + Units.Q_INCH, Units.ETH_INCH), (pan + 3*Units.H_INCH, Units.ETH_INCH))

        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))
        for y in (0, upper_y):
            x = 0
            while x < upper_x+pan:
                for step in ridge_steps:
                    verts.append((x+step[0], y, step[1]))
                x += 2 * Units.INCH

                for _ in range(2):
                    for step in valley_steps:
                        verts.append((x+step[0], y, step[1]))
                    x += pan + 7*Units.Q_INCH

                verts.append((x, y, 0))
                x += pan

        # faces
        offset = len(verts) // 2
        for i in range(offset - 1):
            faces.append((i, i + 1, i + offset + 1, i + offset))

    @staticmethod
    def _tin_standing_seam(props, verts, faces):
        width = props.pan_width
        qi, hi, sqi, fei, tei = Units.Q_INCH, Units.H_INCH, 7*Units.Q_INCH, 5*Units.ETH_INCH, 13*Units.ETH_INCH
        sei, nsi = 7*Units.ETH_INCH, 9*Units.STH_INCH

        v_offset = 11
        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))
        x = 0
        while x < upper_x:
            p = len(verts)
            tx = x
            for y in (0, upper_y):
                verts += [
                    (x+qi, y, qi),
                    (x+hi, y, hi),
                    (x, y, hi),
                    (x, y, sqi),
                    (x+fei, y, sqi),
                    (x+fei, y, 0)
                ]

                x += fei + width
                verts += [
                    (x, y, 0),
                    (x, y, tei),
                    (x-qi, y, tei),
                    (x-qi, y, sei),
                    (x-hi, y, fei)
                ]
                x = tx  # reset back to beginning

            x += fei + width - nsi  # move to next pan

            for i in range(v_offset-1):  # one less face than the number of vertices in pan
                faces.append((p+i, p+i+1, p+i+1+v_offset, p+i+v_offset))

    @staticmethod
    def _shingles_3_tab(props, verts, faces):
        width, exposure, th, gap = Units.FOOT, 11*Units.H_INCH, 5*Units.STH_INCH, Units.H_INCH

        first_length_for_fixed_offset = (width - (gap/2)) * (props.row_offset / 100)
        if first_length_for_fixed_offset == 0:
            first_length_for_fixed_offset = width - (gap/2)

        offset_length_variance = JVRoofing._create_variance_function(props.vary_row_offset, width / 2,
                                                                     props.row_offset_variance)

        # there are three layers for the last bit of the shingle, so 1 1/2 up needs to be at 2th
        bottom_z = (width / (2*exposure)) * 2 * th
        middle_z = bottom_z - th

        # bottom backing row
        verts += [
            (0, 0, bottom_z-th),
            (props.length, 0, bottom_z-th),
            (props.length, exposure, middle_z-th),
            (0, exposure, middle_z-th)
        ]
        faces.append((0, 1, 2, 3))

        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))
        y = 0
        odd = False
        while y < upper_y:
            x = 0
            p = len(verts)
            is_gap = False
            while x < upper_x + width:  # go farther to ensure that last set of vertices is placed
                verts += [
                    (x, y, bottom_z),
                    (x, y+exposure, middle_z),
                    (x, y+width, 0)
                ]

                if is_gap:
                    x += gap
                else:
                    if x == 0:
                        if odd and not props.vary_row_offset:
                            x += first_length_for_fixed_offset
                        elif props.vary_row_offset:
                            x += offset_length_variance()
                        else:
                            x += width - (gap / 2)
                    else:
                        x += width - (gap / 2)

                is_gap = not is_gap
            odd = not odd
            y += exposure

            # faces, connect in two possible ways, depending on whether it is a gap or not
            sets = (len(verts) - p) // 3  # each set contains 3 vertices
            is_gap = False
            for i in range(0, 3*(sets - 1), 3):  # do one less set to just fill between sets
                if is_gap:
                    faces.append((p+i+1, p+i+4, p+i+5, p+i+2))
                else:
                    faces.extend(((p+i, p+i+3, p+i+4, p+i+1), (p+i+1, p+i+4, p+i+5, p+i+2)))

                is_gap = not is_gap
