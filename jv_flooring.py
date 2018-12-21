from . jv_builder_base import JVBuilderBase


class JVFlooring(JVBuilderBase):
    @staticmethod
    def draw(props, layout):
        layout.prop(props, "flooring_pattern", icon="MESH_GRID")

        layout.separator()
        row = layout.row()
        row.prop(props, "width")
        row.prop(props, "length")

        layout.separator()
        row = layout.row()

        # length and width - wood-like
        if props.flooring_pattern == "regular":
            row.prop(props, "board_width_medium")
            row.prop(props, "board_length_medium")
        elif props.flooring_pattern in ("herringbone", "chevron"):
            row.prop(props, "board_width_narrow")
            row.prop(props, "board_length_short")
        elif props.flooring_pattern == "checkerboard":
            row.prop(props, "board_length_really_short")
            row.prop(props, "checkerboard_board_count")
        # tile-like
        elif props.flooring_pattern == "hexagons":
            row.prop(props, "tile_width")
        else:  # hopscotch, windmill, stepping_stone, corridor
            row.prop(props, "tile_width")
            row.prop(props, "tile_length")

        # length and width variance
        if props.flooring_pattern == "regular":
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

            # row offset
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_row_offset", icon="RNDCURVE")
            if props.vary_row_offset:
                row.prop(props, "row_offset_variance")
            else:
                row.prop(props, "row_offset")

        # thickness and variance
        layout.separator()
        layout.prop(props, "thickness")

        row = layout.row()
        row.prop(props, "vary_thickness", icon="RNDCURVE")
        if props.vary_thickness:
            row.prop(props, "thickness_variance")

        # gaps
        layout.separator()
        row = layout.row()
        row.prop(props, "gap_uniform")

    @staticmethod
    def update(props, context):
        mesh = JVFlooring._start(context)
        verts, faces = JVFlooring._geometry(props)

        mesh.clear()
        for v in verts:
            mesh.verts.new(v)
        mesh.verts.ensure_lookup_table()

        for f in faces:
            mesh.faces.new([mesh.verts[i] for i in f])
        mesh.faces.ensure_lookup_table()

        # solidify
        JVFlooring._solidfy(mesh, (0, 0, 1), JVFlooring._create_variance_function(props.vary_thickness, props.thickness,
                                                                                  props.thickness_variance))

        JVFlooring._finish(context, mesh)

    @staticmethod
    def _geometry(props):
        verts, faces = [], []

        # dynamically call correct method as their names will match up with the style name
        getattr(JVFlooring, "_{}".format(props.flooring_pattern))(props, verts, faces)

        return verts, faces

    @staticmethod
    def _regular(props, verts, faces):
        width_variance = JVFlooring._create_variance_function(props.vary_width, props.board_width_narrow,
                                                              props.width_variance)
        length_variance = JVFlooring._create_variance_function(props.vary_length, props.board_length_medium,
                                                               props.length_variance)

        first_length_for_fixed_offset = props.board_length_medium * (props.row_offset / 100)
        if first_length_for_fixed_offset == 0:
            first_length_for_fixed_offset = props.board_length_medium

        offset_length_variance = JVFlooring._create_variance_function(props.vary_row_offset,
                                                                      props.board_length_medium / 2,
                                                                      props.row_offset_variance)

        y = 0
        odd = False
        upper_x, upper_y = props.length, props.width
        while y < upper_y:
            x = 0

            width = width_variance()
            while x < upper_x:
                length = length_variance()
                if x == 0:  # first board
                    if props.vary_row_offset:
                        length = offset_length_variance()
                    elif odd:
                        length = first_length_for_fixed_offset

                trimmed_width = min(width, upper_y-y)
                trimmed_length = min(length, upper_x-x)

                verts += [
                    (x, y, 0),
                    (x+trimmed_length, y, 0),
                    (x+trimmed_length, y+trimmed_width, 0),
                    (x, y+trimmed_width, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+1, p+2, p+3))

                x += length + props.gap_uniform

            y += width + props.gap_uniform
            odd = not odd

    @staticmethod
    def _checkerboard(props, verts, faces):
        length = props.board_length_really_short
        board_count = props.checkerboard_board_count
        gap = props.gap_uniform

        # the width of each board so that the total of them is the same as the length
        width = (length - (gap * (board_count - 1))) / board_count

        y = 0
        upper_x, upper_y = props.length, props.width
        start_vertical = False
        while y < upper_y:
            x = 0

            vertical = start_vertical
            while x < upper_x:
                if vertical:
                    for _ in range(board_count):
                        if x < upper_x:
                            # width is paired with x and length with y because board is rotated
                            trimmed_width = min(width, upper_x-x)
                            trimmed_length = min(length, upper_y-y)

                            verts += [
                                (x, y, 0),
                                (x+trimmed_width, y, 0),
                                (x+trimmed_width, y+trimmed_length, 0),
                                (x, y+trimmed_length, 0)
                            ]

                            p = len(verts) - 4
                            faces.append((p, p+1, p+2, p+3))

                            x += width + gap
                else:
                    ty = y
                    for _ in range(board_count):
                        if ty < upper_y:
                            # width is paired with x and length with y because board is rotated
                            trimmed_width = min(width, upper_y - ty)
                            trimmed_length = min(length, upper_x - x)

                            verts += [
                                (x, ty, 0),
                                (x + trimmed_length, ty, 0),
                                (x + trimmed_length, ty + trimmed_width, 0),
                                (x, ty + trimmed_width, 0)
                            ]

                            p = len(verts) - 4
                            faces.append((p, p + 1, p + 2, p + 3))

                            ty += width + gap
                    x += length + gap

                vertical = not vertical

            y += length + gap
            start_vertical = not start_vertical
