from . jv_builder_base import JVBuilderBase
from . jv_utils import Units
from mathutils import Vector, Euler
from math import atan, radians, sqrt, sin, cos
import bmesh


class JVSiding(JVBuilderBase):
    @staticmethod
    def draw(props, layout):
        layout.prop(props, "siding_pattern", icon="MOD_TRIANGULATE")

        layout.separator()
        row = layout.row()
        row.prop(props, "height")
        row.prop(props, "length")
        layout.separator()

        if props.siding_pattern in ("regular", "shiplap", "dutch_lap", "clapboard"):
            row = layout.row()
            row.prop(props, "board_width_medium")
            row.prop(props, "board_length_long")
        elif props.siding_pattern == "brick":
            row = layout.row()
            row.prop(props, "brick_height")
            row.prop(props, "brick_length")
        elif props.siding_pattern in ("shakes", "scallop_shakes"):
            row = layout.row()
            row.prop(props, "shake_length")
            row.prop(props, "shake_width")

        if props.siding_pattern in ("regular", "shiplap"):
            layout.separator()
            layout.prop(props, "siding_direction", icon="ORIENTATION_VIEW")

        if props.siding_pattern == "dutch_lap":
            layout.separator()
            layout.prop(props, "dutch_lap_breakpoint")

        # width variance
        if props.siding_pattern in ("regular", "shiplap", "dutch_lap", "clapboard", "shakes"):
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_width", icon="RNDCURVE")
            if props.vary_width:
                row.prop(props, "width_variance")

        # length variance
        if props.siding_pattern in ("regular", "shiplap", "dutch_lap", "clapboard"):
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_length", icon="RNDCURVE")
            if props.vary_length:
                row.prop(props, "length_variance")

        # scallop resolution
        if props.siding_pattern == "scallop_shakes":
            layout.separator()
            layout.prop(props, "scallop_resolution")

        # battens
        if props.siding_pattern == "regular" and props.siding_direction == "vertical":
            layout.separator()
            box = layout.box()
            box.prop(props, "battens", icon="SNAP_EDGE")

            if props.battens:
                box.separator()
                box.prop(props, "batten_width")

                row = box.row()
                row.prop(props, "vary_batten_width", icon="RNDCURVE")
                if props.vary_batten_width:
                    row.prop(props, "batten_width_variance")

        # jointing
        if props.siding_pattern == "brick":
            layout.separator()
            row = layout.row()
            row.prop(props, "joint_left", icon="ALIGN_RIGHT")
            row.prop(props, "joint_right", icon="ALIGN_LEFT")

        # row offset
        if props.siding_pattern in ("shakes", "scallop_shakes") or \
                (props.siding_pattern == "brick" and not props.joint_right and not props.joint_left):
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_row_offset", icon="RNDCURVE")
            if props.vary_row_offset:
                row.prop(props, "row_offset_variance")
            else:
                row.prop(props, "row_offset")

        # thickness and variance
        if props.siding_pattern not in ("tin_regular", "tin_angular"):
            layout.separator()
            box = layout.box()

            if props.siding_pattern == "brick":
                box.prop(props, "thickness_thick")
            elif props.siding_pattern in ("clapboard", "shakes", "scallop_shakes"):
                box.prop(props, "thickness_thin")
            else:
                box.prop(props, "thickness")

            # NOTE: we cannot have varying thickness if battens are involved
            if props.siding_pattern in ("dutch_lap", "brick", "shiplap") or \
                    (props.siding_pattern == "regular" and not props.battens):
                row = box.row()
                row.prop(props, "vary_thickness", icon="RNDCURVE")
                if props.vary_thickness:
                    row.prop(props, "thickness_variance")

        # gaps
        if props.siding_pattern in ("regular", "dutch_lap", "clapboard", "brick", "shakes", "scallop_shakes"):
            layout.separator()
            row = layout.row()
            row.prop(props, "gap_uniform")
        elif props.siding_pattern == "shiplap":
            layout.separator()
            row = layout.row()
            row.prop(props, "gap_widthwise")
            row.prop(props, "gap_lengthwise")

        # grout/mortar
        if props.siding_pattern == "brick":
            layout.separator()
            row = layout.row()
            row.prop(props, "add_grout", text="Add Mortar?", icon="MOD_WIREFRAME")
            if props.add_grout:
                row.prop(props, "grout_depth", text="Mortar Depth")

        # slope
        layout.separator()
        box = layout.box()
        row = box.row()
        row.prop(props, "slope_top", icon="LINCURVE")
        if props.slope_top:
            row.prop(props, "pitch")
            box.row().prop(props, "pitch_offset")

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

        if props.add_cutouts:
            JVSiding._cutouts(mesh, props)

        original_edges = mesh.edges[:]

        # create mortar mesh
        mortar_mesh = None
        mortar_original_edges = []
        if props.siding_pattern == "brick" and props.add_grout:
            mortar_mesh = bmesh.new()

            # account for jointing
            th = props.thickness_thick * (1 - (props.grout_depth / 100)) + props.gap_uniform
            lx = th if props.joint_left else 0
            rx = th if props.joint_right else 0

            for v in ((-lx, 0, 0), (props.length+rx, 0, 0), (props.length+rx, 0, props.height), (-lx, 0, props.height)):
                mortar_mesh.verts.new(v)
            mortar_mesh.verts.ensure_lookup_table()

            mortar_mesh.faces.new([mortar_mesh.verts[i] for i in (0, 3, 2, 1)])
            mortar_mesh.faces.ensure_lookup_table()

            mortar_original_edges = mortar_mesh.edges[:]

        # cut top and right
        if props.siding_pattern in ("dutch_lap", "shiplap", "tin_regular", "tin_angular", "scallop_shakes"):
            JVSiding._cut_meshes([mesh], [
                ((0, 0, props.height), (0, 0, -1)),  # top
                ((props.length, 0, 0), (-1, 0, 0))  # right
            ])

        # cut left
        if props.siding_pattern == "scallop_shakes":
            JVSiding._cut_meshes([mesh], [((0, 0, 0), (1, 0, 0))])

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

            meshes = [mesh]
            if mortar_mesh is not None:
                meshes.append(mortar_mesh)

            JVSiding._cut_meshes(meshes, [
                (center, left_normal),
                (center, right_normal)
            ])

        new_geometry = []
        # solidify - add thickness to props.thickness level
        if props.siding_pattern in ("regular", "brick"):
            th = props.thickness_thick if props.siding_pattern == "brick" else props.thickness
            new_geometry += JVSiding._solidify(mesh,
                                               JVSiding._create_variance_function(props.vary_thickness, th,
                                                                                  props.thickness_variance))
        # solidify - add thickness, non-variable
        elif props.siding_pattern in ("clapboard", "shakes", "scallop_shakes"):
            new_geometry += JVSiding._solidify(mesh, props.thickness_thin)

        # solidify - just add slight thickness
        elif props.siding_pattern == "dutch_lap":
            new_geometry += JVSiding._solidify(mesh, Units.ETH_INCH)

        # add main material index
        JVSiding._add_material_index(mesh.faces, 0)

        # solidify mortar
        if mortar_mesh is not None:
            th = props.thickness_thick * (1 - (props.grout_depth / 100))
            mortar_new_geometry = JVSiding._solidify(mortar_mesh, th)

            # merge mortar mesh
            mappings = {}
            for v in mortar_mesh.verts:
                mappings[v] = mesh.verts.new(v.co)
            mesh.verts.ensure_lookup_table()

            new_edges = set()  # should have a size of 12
            face_mappings = {}
            for f in mortar_mesh.faces:
                face = mesh.faces.new([mappings[v] for v in f.verts])
                face_mappings[f] = face
                face.material_index = 1

                for edge in face.edges:
                    new_edges.add(edge)
            mesh.faces.ensure_lookup_table()

            mortar_mesh.free()

            # determine where mortar_original_edges and mortar_new_geometry mapped in mesh.edges to all uv_seam handling
            for edge in mortar_original_edges:  # should run 4*12 times in total
                # find where edge maps
                for cor_edge in new_edges:
                    e1, e2 = mappings[edge.verts[0]], mappings[edge.verts[1]]
                    ce1, ce2 = cor_edge.verts
                    if (e1 is ce1 and e2 is ce2) or (e1 is ce2 and e2 is ce1):
                        original_edges.append(cor_edge)

            # map the extruded face to the corresponding face in the new mesh
            for item in mortar_new_geometry:
                if isinstance(item, bmesh.types.BMFace):
                    new_geometry.append(face_mappings[item])

        # add uv seams
        if props.siding_pattern != "shiplap":
            JVSiding._add_uv_seams_for_solidified_plane(new_geometry, original_edges, mesh)

        JVSiding._finish(context, mesh)

    @staticmethod
    def _geometry(props):
        verts, faces = [], []

        # dynamically call correct method as their names will match up with the style name
        getattr(JVSiding, "_{}".format(props.siding_pattern))(props, verts, faces)

        return verts, faces

    @staticmethod
    def _regular(props, verts, faces):
        length, width, gap = props.board_length_long, props.board_width_medium, props.gap_uniform
        batten_width, by = props.batten_width, -props.thickness

        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        batten_width_variance = JVSiding._create_variance_function(props.vary_batten_width, batten_width,
                                                                   props.batten_width_variance)
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
                    faces.append((p, p+3, p+2, p+1))

                    z += cur_length + gap
                x += cur_width + gap

                # battens
                if props.battens and not props.vary_thickness:
                    bw = batten_width_variance()
                    tx = x - (gap / 2) - (bw / 2)

                    if tx < upper_x:
                        bw = min(bw, upper_x-tx)
                        tz = 0
                        while tz < upper_z:
                            bl = length_variance()
                            bl = min(bl, upper_z-tz)

                            verts += [
                                (tx, by, tz),
                                (tx+bw, by, tz),
                                (tx+bw, by, tz+bl),
                                (tx, by, tz+bl)
                            ]

                            p = len(verts) - 4
                            faces.append((p, p+3, p+2, p+1))

                            tz += bl + gap

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
                    faces.append((p, p+3, p+2, p+1))

                    x += cur_length + gap
                z += cur_width + gap

    @staticmethod
    def _dutch_lap(props, verts, faces):
        length, width, gap, th = props.board_length_long, props.board_width_medium, props.gap_uniform, props.thickness
        break_p = props.dutch_lap_breakpoint / 100

        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        thickness_variance = JVSiding._create_variance_function(props.vary_thickness, th, props.thickness_variance)

        z = 0
        upper_x, upper_z = props.length, props.height
        while z < upper_z:
            x = 0

            cur_width = width_variance()
            break_width = cur_width * break_p
            y = thickness_variance()  # do thickness per row
            while x < upper_x:
                cur_length = length_variance()

                for xx in (x, x+cur_length):
                    verts += [
                        (xx, 0, z),
                        (xx, -y, z),
                        (xx, -y, z+break_width),
                        (xx, 0, z+cur_width)
                    ]

                p = len(verts) - 8
                faces.extend((
                    (p, p+1, p+5, p+4),
                    (p+1, p+2, p+6, p+5),
                    (p+2, p+3, p+7, p+6)
                ))

                x += cur_length + gap
            z += cur_width + Units.ETH_INCH  # shift up width + thickness

    @staticmethod
    def _shiplap(props, verts, faces):
        length, width, th = props.board_length_long, props.board_width_medium, props.thickness
        gap_length, gap_width = props.gap_lengthwise, props.gap_widthwise

        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        thickness_variance = JVSiding._create_variance_function(props.vary_thickness, th, props.thickness_variance)

        upper_x, upper_z = props.length, props.height
        if props.siding_direction == "vertical":
            x = 0
            while x < upper_x:
                z = 0
                dx, y = width_variance(), -thickness_variance()
                while z < upper_z:
                    dz = length_variance()

                    p = len(verts)
                    for zz in (z, z+dz):
                        verts += [
                            (x, 0, zz),
                            (x, y, zz),
                            (x+dx, y, zz),
                            (x+dx, 0, zz),
                            (x+dx+gap_width, 0, zz)
                        ]

                    # faces
                    for _ in range(4):
                        faces.append((p, p+1, p+6, p+5))
                        p += 1

                    z += dz + gap_length
                x += dx + gap_width
        else:
            z = 0
            while z < upper_z:
                x = 0
                dz, y = width_variance(), -thickness_variance()
                while x < upper_x:
                    dx = length_variance()

                    p = len(verts)
                    for xx in (x, x+dx):
                        verts += [
                            (xx, 0, z),
                            (xx, y, z),
                            (xx, y, z+dz),
                            (xx, 0, z+dz),
                            (xx, 0, z+dz+gap_width)
                        ]

                    # faces
                    for _ in range(4):
                        faces.append((p, p+1, p+6, p+5))
                        p += 1

                    x += dx + gap_length
                z += dz + gap_width

    @staticmethod
    def _clapboard(props, verts, faces):
        length, width, gap = props.board_length_long, props.board_width_medium, props.gap_uniform
        th = props.thickness_thin
        length_variance = JVSiding._create_variance_function(props.vary_length, length, props.length_variance)
        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)

        z = 0
        upper_x, upper_z = props.length, props.height
        while z < upper_z:
            x = 0

            vertical_width = sqrt(width_variance()**2 - th**2)
            while x < upper_x:
                length = length_variance()

                trimmed_length = min(length, upper_x-x)
                trimmed_width = min(vertical_width, upper_z-z)

                verts += [
                    (x, -th, z),
                    (x+trimmed_length, -th, z),
                    (x+trimmed_length, 0, z+trimmed_width),
                    (x, 0, z+trimmed_width)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += length + gap
            z += vertical_width

    @staticmethod
    def _tin_regular(props, verts, faces):
        ridge_steps = (
            (0, 0),
            (Units.H_INCH, Units.TQ_INCH),
            (5*Units.ETH_INCH, 7*Units.ETH_INCH),
            (11*Units.STH_INCH, Units.INCH),
            (17*Units.STH_INCH, Units.INCH),
            (9*Units.ETH_INCH, 7*Units.ETH_INCH),
            (5*Units.Q_INCH, 3*Units.Q_INCH)
        )

        valley_steps = (
            (0, 0),
            (13*Units.ETH_INCH, 0),
            (15*Units.ETH_INCH, Units.ETH_INCH),
            (21*Units.ETH_INCH, Units.ETH_INCH)
        )

        upper_x = props.length
        offset_between_valley_accents = 23*Units.ETH_INCH
        for z in (0, props.height):
            x = 0
            while x < upper_x+offset_between_valley_accents:
                for step in ridge_steps:
                    verts.append((x+step[0], -step[1], z))
                x += 7*Units.Q_INCH

                for _ in range(2):
                    for step in valley_steps:
                        verts.append((x+step[0], -step[1], z))
                    x += offset_between_valley_accents

                verts.append((x, 0, z))  # finish valley ridge
                x += offset_between_valley_accents-Units.INCH

        # faces
        offset = len(verts) // 2
        for i in range(offset-1):
            faces.append((i, i+1, i+offset+1, i+offset))

    @staticmethod
    def _tin_angular(props, verts, faces):
        pan = 3*Units.INCH
        ridge_steps = ((0, 0), (Units.H_INCH, 5*Units.Q_INCH), (3*Units.H_INCH, 5*Units.Q_INCH), (2*Units.INCH, 0))
        valley_steps = ((0, 0), (pan, 0), (pan + Units.Q_INCH, Units.ETH_INCH), (pan + 3*Units.H_INCH, Units.ETH_INCH))

        upper_x = props.length
        for z in (0, props.height):
            x = 0
            while x < upper_x+pan:
                for step in ridge_steps:
                    verts.append((x+step[0], -step[1], z))
                x += 2 * Units.INCH

                for _ in range(2):
                    for step in valley_steps:
                        verts.append((x+step[0], -step[1], z))
                    x += pan + 7*Units.Q_INCH

                verts.append((x, 0, z))
                x += pan

        # faces
        offset = len(verts) // 2
        for i in range(offset - 1):
            faces.append((i, i + 1, i + offset + 1, i + offset))

    @staticmethod
    def _brick(props, verts, faces):
        length, height, gap, th = props.brick_length, props.brick_height, props.gap_uniform, props.thickness_thick

        first_length_for_fixed_offset = length * (props.row_offset / 100)
        if first_length_for_fixed_offset == 0:
            first_length_for_fixed_offset = length

        offset_length_variance = JVSiding._create_variance_function(props.vary_row_offset, length / 2,
                                                                    props.row_offset_variance)

        z = 0
        odd = False
        upper_x, upper_z = props.length, props.height
        while z < upper_z:
            if odd and props.joint_left:
                x = -th - gap
            else:
                x = 0

            trimmed_height = min(height, upper_z-z)
            while x < upper_x:
                cur_length = length
                if x == 0:
                    if odd and not props.vary_row_offset:
                        cur_length = first_length_for_fixed_offset
                    elif props.vary_row_offset:
                        cur_length = offset_length_variance()

                if not odd and props.joint_right:
                    trimmed_length = min(cur_length, upper_x + th + gap - x)
                else:
                    trimmed_length = min(cur_length, upper_x - x)

                verts += [
                    (x, 0, z),
                    (x+trimmed_length, 0, z),
                    (x+trimmed_length, 0, z+trimmed_height),
                    (x, 0, z+trimmed_height)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += cur_length + gap
            z += height + gap
            odd = not odd

    @staticmethod
    def _shakes(props, verts, faces):
        length, width, gap = props.shake_length, props.shake_width, props.gap_uniform
        th_y, hl = -2 * props.thickness_thin, length / 2

        first_width_for_fixed_offset = width * (props.row_offset / 100)
        if first_width_for_fixed_offset == 0:
            first_width_for_fixed_offset = width

        offset_width_variance = JVSiding._create_variance_function(props.vary_row_offset, width / 2,
                                                                   props.row_offset_variance)
        width_variance = JVSiding._create_variance_function(props.vary_width, width, props.width_variance)
        upper_x, upper_z = props.length, props.height

        # bottom row backing layer
        verts += [
            (0, th_y / 2, 0),
            (upper_x, th_y / 2, 0),
            (upper_x, 0, hl),
            (0, 0, hl)
        ]
        faces.append((0, 3, 2, 1))

        z = 0
        odd = False
        while z < upper_z:
            x = 0

            while x < upper_x:
                cur_width = width_variance()
                if x == 0:
                    if odd and not props.vary_row_offset:
                        cur_width = first_width_for_fixed_offset
                    elif props.vary_row_offset:
                        cur_width = offset_width_variance()

                dx = min(cur_width, upper_x-x)
                dz = min(length, upper_z-z)

                verts += [
                    (x, th_y, z),
                    (x+dx, th_y, z),
                    (x+dx, 0, z+dz),
                    (x, 0, z+dz)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += cur_width + gap
            z += hl
            odd = not odd

    @staticmethod
    def _scallop_shakes(props, verts, faces):
        length, width, gap, th = props.shake_length, props.shake_width, props.gap_uniform, props.thickness_thin
        rad, res = width / 2, props.scallop_resolution
        rest_z, ang_step = length - rad, radians(180 / (res+1))
        th_y, y_slope = -th, -th / rest_z

        first_width_for_fixed_offset = width * (props.row_offset / 100)
        if first_width_for_fixed_offset == width:
            first_width_for_fixed_offset = 0

        offset_width_variance = JVSiding._create_variance_function(props.vary_row_offset, width / 2,
                                                                   props.row_offset_variance)

        upper_x, upper_z = props.length, props.height
        odd = False
        z = rad
        while z < upper_z:
            x = 0
            if odd and not props.vary_row_offset:
                x = -first_width_for_fixed_offset
            elif props.vary_row_offset:
                x = -offset_width_variance()

            while x < upper_x:
                cx = x + rad
                top = z+rest_z
                p = len(verts)
                for i in range(res+2):
                    ang = ang_step * i
                    dx = rad * cos(ang)
                    dz = rad * sin(ang)

                    verts += [(cx-dx, th_y + (y_slope*dz), z-dz), (cx-dx, 0, top)]

                # faces
                for i in range(res+1):
                    faces.append((p, p+1, p+3, p+2))
                    p += 2

                x += width + gap
            odd = not odd
            z += rest_z
