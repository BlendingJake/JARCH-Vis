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
        if props.flooring_style in ("wood_regular", "tile_regular"):
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

        if props.flooring_style == "wood_regular":
            JVFlooring._wood_regular(props, verts, faces)

        return verts, faces

    @staticmethod
    def _wood_regular(props, verts, faces):
        x = 0
        width_variance = JVFlooring._create_variance_function(props.vary_width, props.board_width, props.width_variance)
        length_variance = JVFlooring._create_variance_function(props.vary_length, props.board_length,
                                                               props.length_variance)

        while x < props.width:
            y = 0

            width = width_variance()
            if x + width > props.width:
                width = props.width - x

            while y < props.length:
                length = length_variance()
                if y + length > props.length:
                    length = props.length - y

                verts += [
                    (x, y, 0),
                    (x+width, y, 0),
                    (x+width, y+length, 0),
                    (x, y+length, 0)
                ]

                i = len(verts) - 4
                faces.append((i, i+1, i+2, i+3))

                y += length + props.gap_lengthwise

            x += width + props.gap_widthwise
