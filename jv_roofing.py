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

        if props.roofing_pattern == "tin_standing_seam":
            layout.separator()
            layout.prop(props, "pan_width")
        elif props.roofing_pattern == "shakes":
            layout.separator()
            row = layout.row()
            row.prop(props, "shake_length")
            row.prop(props, "shake_width")

        # row offset
        if props.roofing_pattern in ("shingles_3_tab", "shakes"):
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_row_offset", icon="RNDCURVE")
            if props.vary_row_offset:
                row.prop(props, "row_offset_variance")
            else:
                row.prop(props, "row_offset")

        # thickness
        if props.roofing_pattern in ("shingles_3_tab", "shingles_architectural", "shakes"):
            layout.separator()
            layout.prop(props, "thickness_thin")

        # gap
        if props.roofing_pattern == "shakes":
            layout.separator()
            layout.prop(props, "gap_uniform")

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
        if props.roofing_pattern in ("tin_regular", "tin_angular", "tin_standing_seam", "shingles_3_tab",
                                     "shingles_architectural"):
            JVRoofing._cut_meshes([mesh], [
                ((props.length, 0, 0), (-1, 0, 0))
            ])
        # overall dimension cutting - width
        if props.roofing_pattern in ("shingles_3_tab", "shingles_architectural"):
            JVRoofing._cut_meshes([mesh], [
                ((0, props.width / cos(atan(props.pitch / 12)), 0), (0, -1, 0))
            ])

        # rotate
        rot = atan(props.pitch / 12)
        rotation = Euler((rot, 0, 0))
        JVRoofing._rotate_mesh_vertices(mesh, rotation)

        # mirror

        # solidify
        if props.roofing_pattern in ("shingles_3_tab", "shingles_architectural", "shakes"):
            JVRoofing._solidify(mesh, JVRoofing._create_variance_function(False, props.thickness_thin, 0))

        # main material index
        JVRoofing._add_material_index(mesh.faces, 0)

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
        width, exposure, th, gap = Units.FOOT, 11*Units.H_INCH, props.thickness_thin, Units.H_INCH

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

    @staticmethod
    def _shingles_architectural(props, verts, faces):
        hi, th, width = Units.H_INCH, props.thickness_thin, Units.FOOT
        hw = width / 2

        bottom_z, mid_z = 4*th, 2*th

        separation_variance = JVRoofing._create_variance_function(True, 8*Units.INCH, 40)
        width_variance = JVRoofing._create_variance_function(True, 4*Units.INCH, 60)

        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))
        y = 0
        odd = False
        while y < upper_y:
            # row backing layer
            verts += [
                (0, y, bottom_z),
                (upper_x, y, bottom_z),
                (upper_x, y+width, 0),
                (0, y+width, 0)
            ]

            p = len(verts) - 4
            faces.append((p, p+1, p+2, p+3))

            x = 0
            finish = False
            p = len(verts)
            while x < upper_x or finish:
                finish = False
                dx = separation_variance()
                if x == 0 and odd:
                    dx /= 2

                verts += [  # all z's are +th because they are layered on top of the backing layer
                    (x, y+hw, mid_z+th),
                    (x, y+width, th)
                ]

                x += dx

                if x < upper_x:  # only do tab if we are still under width
                    verts += [
                        (x-hi, y, bottom_z+th),
                        (x, y+hw, mid_z+th),
                        (x, y+width, th)
                    ]

                    x += width_variance()
                    verts.append((x+hi, y, bottom_z+th))
                    finish = True  # if we get here, we need to finish the row no matter what

            # faces
            # there will always be 2 verts on the end to close everything off, besides that, it will be multiple of 6
            sets = (len(verts) - p - 2) // 6
            for i in range(0, 6*sets, 6):
                faces.extend((
                    (p+i, p+i+3, p+i+4, p+i+1),
                    (p+i+2, p+i+5, p+i+6, p+i+3),
                    (p+i+3, p+i+6, p+i+7, p+i+4)
                ))

            y += hw
            odd = not odd

    @staticmethod
    def _shakes(props, verts, faces):
        length, width, gap = props.shake_length, props.shake_width, props.gap_uniform
        th_z, hl = 2 * props.thickness_thin, length / 2

        first_width_for_fixed_offset = width * (props.row_offset / 100)
        if first_width_for_fixed_offset == 0:
            first_width_for_fixed_offset = width

        offset_width_variance = JVRoofing._create_variance_function(props.vary_row_offset, width / 2,
                                                                    props.row_offset_variance)
        width_variance = JVRoofing._create_variance_function(props.vary_width, width, props.width_variance)
        upper_x, upper_y = props.length, props.width / cos(atan(props.pitch / 12))

        # bottom row backing layer
        verts += [
            (0, 0, th_z / 2),
            (upper_x, 0, th_z / 2),
            (upper_x, hl, 0),
            (0, hl, 0)
        ]
        faces.append((0, 1, 2, 3))

        y = 0
        odd = False
        while y < upper_y:
            x = 0

            while x < upper_x:
                cur_width = width_variance()
                if x == 0:
                    if odd and not props.vary_row_offset:
                        cur_width = first_width_for_fixed_offset
                    elif props.vary_row_offset:
                        cur_width = offset_width_variance()

                dx = min(cur_width, upper_x - x)
                dy = min(length, upper_y - y)

                verts += [
                    (x, y, th_z),
                    (x + dx, y, th_z),
                    (x + dx, y + dy, 0),
                    (x, y + dy, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p + 1, p + 2, p + 3))

                x += cur_width + gap
            y += hl
            odd = not odd

