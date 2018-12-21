from . jv_builder_base import JVBuilderBase


class JVFlooring(JVBuilderBase):
    @staticmethod
    def draw(props, layout):
        layout.prop(props, "flooring_style", icon="MESH_GRID")

        layout.separator()
        row = layout.row()
        row.prop(props, "width")
        row.prop(props, "length")

        layout.separator()
        row = layout.row()

        # length and width
        if props.flooring_style == "wood_regular":
            row.prop(props, "board_width")
            row.prop(props, "board_length")
        elif props.flooring_style in ("parquet", "herringbone_parquet", "herringbone"):
            row.prop(props, "board_width_narrow")
            row.prop(props, "board_length_short")
        elif props.flooring_style == "hexagons":
            row.prop(props, "tile_width")
        else:  # tile_regular, tile_large_small, tile_large_many_small
            row.prop(props, "tile_width")
            row.prop(props, "tile_length")

        # length and width variance
        if props.flooring_style == "wood_regular":
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

        # gaps
        layout.separator()
        row = layout.row()
        if props.flooring_style in ("wood_regular", "tile_regular"):
            row.prop(props, "gap_widthwise")
            row.prop(props, "gap_lengthwise")
        else:
            row.prop(props, "gap_uniform")

        # row offset
        if props.flooring_style == "tile_regular":
            layout.separator()
            row = layout.row()

            row.prop(props, "vary_row_offset", icon="RNDCURVE")
            if props.vary_row_offset:
                row.prop(props, "row_offset_variance")
            else:
                row.prop(props, "tile_row_offset")

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
        getattr(JVFlooring, "_{}".format(props.flooring_style))(props, verts, faces)

        return verts, faces

    @staticmethod
    def _wood_regular(props, verts, faces):
        width_variance = JVFlooring._create_variance_function(props.vary_width, props.board_width, props.width_variance)
        length_variance = JVFlooring._create_variance_function(props.vary_length, props.board_length,
                                                               props.length_variance)

        x = 0
        while x < props.width:
            y = 0

            width = width_variance()
            while y < props.length:
                length = length_variance()

                verts, faces = JVFlooring._create_quad(verts, faces, x, y, width, length, props.width, props.length)

                y += length + props.gap_lengthwise
            x += width + props.gap_widthwise

    @staticmethod
    def _tile_regular(props, verts, faces):
        fixed_offset_width = props.tile_width * (props.tile_row_offset / 100)  # fixed offset
        width_variance = JVFlooring._create_variance_function(props.vary_row_offset, props.tile_width / 2,
                                                              props.row_offset_variance)

        # no offset is the same as a full offset
        if fixed_offset_width == 0:
            fixed_offset_width = props.tile_width

        y = 0
        odd = False
        while y < props.length:
            x = 0
            while x < props.width:
                width = props.tile_width
                if x == 0:
                    if props.vary_row_offset:
                        width = width_variance()
                    elif odd:
                        width = fixed_offset_width

                verts, faces = JVFlooring._create_quad(verts, faces, x, y, width, props.tile_length, props.width,
                                                       props.length)

                x += width + props.gap_uniform
            y += props.tile_length + props.gap_uniform
            odd = not odd
