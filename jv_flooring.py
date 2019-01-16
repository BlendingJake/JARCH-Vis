# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from . jv_builder_base import JVBuilderBase
from math import sqrt, cos, tan, radians


class JVFlooring(JVBuilderBase):
    is_cutable = True
    is_convertible = True

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
            row.prop(props, "checkerboard_board_count")
            row.prop(props, "board_length_really_short")
        # tile-like
        elif props.flooring_pattern == "windmill":
            row.prop(props, "tile_width")
        elif props.flooring_pattern in ("hexagons", "octagons"):
            row.prop(props, "side_length")
        else:  # hopscotch, stepping_stone, corridor
            row.prop(props, "tile_width")
            row.prop(props, "tile_length")

        if props.flooring_pattern == "corridor":
            layout.prop(props, "alternating_row_width")

        if props.flooring_pattern == "hexagons":
            layout.prop(props, "with_dots", icon="ACTION")

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

        if props.flooring_pattern in ("regular", "corridor"):
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
        box = layout.box()
        box.prop(props, "thickness")

        row = box.row()
        row.prop(props, "vary_thickness", icon="RNDCURVE")
        if props.vary_thickness:
            row.prop(props, "thickness_variance")

        # gaps
        layout.separator()
        row = layout.row()
        row.prop(props, "gap_uniform")

    @staticmethod
    def update(props, context):
        if props.convert_source_object is not None:  # then this is a converted object
            mesh = JVFlooring._generate_mesh_from_converted_object(props, context)
        else:
            mesh = JVFlooring._start(context)
            verts, faces = JVFlooring._geometry(props, (props.length, props.width))
            JVFlooring._build_mesh_from_geometry(mesh, verts, faces)

            # cut if needed
            if props.flooring_pattern in ("herringbone", "chevron", "hopscotch", "stepping_stone", "hexagons",
                                          "octagons", "windmill"):
                JVFlooring._cut_meshes([mesh], [
                    ((0, 0, 0), (1, 0, 0)),  # left
                    ((0, 0, 0), (0, 1, 0)),  # bottom
                    ((props.length, 0, 0), (-1, 0, 0)),  # right
                    ((0, props.width, 0), (0, -1, 0))  # top
                ])

        if props.add_cutouts:
                JVFlooring._cutouts(mesh, props, context.object.matrix_world)

        original_edges = mesh.edges[:]  # used to determine where seams should be added

        # solidify
        new_geometry = JVFlooring._solidify(mesh,
                                            JVFlooring._create_variance_function(props.vary_thickness,
                                                                                 props.thickness,
                                                                                 props.thickness_variance))

        # main material index
        JVFlooring._add_material_index(mesh.faces, 0)

        # add uv seams
        JVFlooring._add_uv_seams_for_solidified_plane(new_geometry, original_edges, mesh)

        JVFlooring._finish(context, mesh)
        JVFlooring._uv_unwrap()

    @staticmethod
    def _geometry(props, dims: tuple):
        verts, faces = [], []

        # dynamically call correct method as their names will match up with the style name
        getattr(JVFlooring, "_{}".format(props.flooring_pattern))(dims, props, verts, faces)

        return verts, faces

    @staticmethod
    def _regular(dims: tuple, props, verts, faces):
        width_variance = JVFlooring._create_variance_function(props.vary_width, props.board_width_medium,
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
        upper_x, upper_y = dims
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
                faces.append((p, p+3, p+2, p+1))

                x += length + props.gap_uniform

            y += width + props.gap_uniform
            odd = not odd

    @staticmethod
    def _checkerboard(dims: tuple, props, verts, faces):
        length = props.board_length_really_short
        board_count = props.checkerboard_board_count
        gap = props.gap_uniform

        # the width of each board so that the total of them is the same as the length
        width = (length - (gap * (board_count - 1))) / board_count

        y = 0
        upper_x, upper_y = dims
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
                            faces.append((p, p+3, p+2, p+1))

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
                            faces.append((p, p+3, p+2, p+1))

                            ty += width + gap
                    x += length + gap

                vertical = not vertical

            y += length + gap
            start_vertical = not start_vertical

    @staticmethod
    def _herringbone(dims: tuple, props, verts, faces):
        length = props.board_length_short
        width = props.board_width_narrow

        # boards oriented at 45 degree angle
        leg_length = length / sqrt(2)
        leg_width = width / sqrt(2)
        leg_gap = props.gap_uniform / sqrt(2)
        long_leg_gap = props.gap_uniform * sqrt(2)

        start_y = -leg_length  # start down some so there are no gaps
        upper_x, upper_y = dims
        while start_y < upper_y + leg_width:  # go a little further than need to ensure no gaps
            x = 0

            y = start_y
            while x < upper_x:
                # board width positive slope - starting from bottom-most corner
                verts += [
                    (x, y, 0),
                    (x+leg_length, y+leg_length, 0),
                    (x+leg_length-leg_width, y+leg_length+leg_width, 0),
                    (x-leg_width, y+leg_width, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                # move to left-most corner of complementary board
                x += leg_length + leg_gap - leg_width
                y += leg_length - leg_gap - leg_width

                # board with negative slope - starting from left-most corner
                verts += [
                    (x, y, 0),
                    (x + leg_length, y - leg_length, 0),
                    (x + leg_length + leg_width, y - leg_length + leg_width, 0),
                    (x + leg_width, y + leg_width, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                # move to bottom-most corner of next board
                x += leg_length + leg_width + leg_gap
                y += -leg_length + leg_width + leg_gap

            start_y += 2 * leg_width + long_leg_gap

    @staticmethod
    def _chevron(dims: tuple, props, verts, faces):
        leg_length = props.board_length_short / sqrt(2)
        leg_width = props.board_width_narrow * sqrt(2)
        leg_gap = props.gap_uniform * sqrt(2)

        start_y = -leg_length
        upper_x, upper_y = dims
        while start_y < upper_y:
            x = 0
            y = start_y

            y_leg_length = leg_length
            while x < upper_x:
                verts += [
                    (x, y, 0),
                    (x+leg_length, y+y_leg_length, 0),
                    (x+leg_length, y+y_leg_length+leg_width, 0),
                    (x, y+leg_width, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += leg_length + props.gap_uniform
                y += y_leg_length

                y_leg_length *= -1  # next board will have opposite slope

            start_y += leg_width + leg_gap

    @staticmethod
    def _hopscotch(dims: tuple, props, verts, faces):
        """
        A row consists of every group that is at the same y value. A row is built, then the x offset for the next
        row is determined and that row is created
        """
        length, width, gap = props.tile_length, props.tile_width, props.gap_uniform
        half_length, half_width = (length - gap) / 2, (width - gap) / 2

        # the actual distance += half_length + gap, but x is moved that much between creating the two tiles
        distance_between_groups = (2 * gap) + (2 * length)

        x_start_values = [  # there are 5 different rows, each with a different starting x value
            -gap - length - gap - half_length,  # orange
            0,  # pink
            -(length / 2) - gap - half_length - (gap / 2),  # yellow
            -(2 * gap) - (2*length),  # green
            -gap - half_length  # blue
        ]

        row = 0
        y = -gap - half_width
        upper_x, upper_y = dims
        while y < upper_y:
            x = x_start_values[row % len(x_start_values)]

            while x < upper_x:
                verts += [  # small tile
                    (x, y, 0),
                    (x+half_length, y, 0),
                    (x+half_length, y+half_width, 0),
                    (x, y+half_width, 0)
                ]

                x += half_length + gap

                verts += [  # large tile
                    (x, y, 0),
                    (x + length, y, 0),
                    (x + length, y + width, 0),
                    (x, y + width, 0)
                ]

                p = len(verts) - 8
                faces.extend(((p, p+3, p+2, p+1), (p+4, p+7, p+6, p+5)))

                x += distance_between_groups

            # we've finished the row, make sure we start in the right place next time
            y += half_width + gap
            row += 1

    @staticmethod
    def _windmill(dims: tuple, props, verts, faces):
        length = props.tile_width
        gap = props.gap_uniform
        width = (length - gap) / 2

        y = 0
        upper_x, upper_y = dims
        while y < upper_y:
            x = 0
            while x < upper_x:
                verts += [
                    (x, y, 0),  # bottom - horizontal
                    (x+length, y, 0),
                    (x+length, y+width, 0),
                    (x, y+width, 0),

                    (x, y+width+gap, 0),  # left - vertical
                    (x+width, y+width+gap, 0),
                    (x+width, y+width+gap+length, 0),
                    (x, y+width+gap+length, 0),

                    (x+width+gap, y+length+gap, 0),  # top - horizontal
                    (x+length+gap+width, y+length+gap, 0),
                    (x+length+gap+width, y+length+gap+width, 0),
                    (x+width+gap, y+length+gap+width, 0),

                    (x+length+gap, y, 0),  # right - vertical
                    (x+length+gap+width, y, 0),
                    (x+length+gap+width, y+length, 0),
                    (x+length+gap, y+length, 0),

                    (x+width+gap, y+width+gap, 0),  # center
                    (x+length, y+width+gap, 0),
                    (x+length, y+length, 0),
                    (x+width+gap, y+length, 0)
                ]

                p = len(verts)
                for i in range(p-20, p, 4):
                    faces.append((i, i+3, i+2, i+1))

                x += length + gap + width + gap
            y += length + gap + width + gap

    @staticmethod
    def _stepping_stone(dims: tuple, props, verts, faces):
        length, width, gap = props.tile_length, props.tile_width, props.gap_uniform
        half_length, half_width = (length - gap) / 2, (width - gap) / 2

        y = 0
        upper_x, upper_y = dims
        while y < upper_y:
            x = 0
            while x < upper_x:
                tx = x
                ty = y
                for _ in range(3):  # three tiles along the bottom
                    verts += [
                        (x, y, 0),
                        (x+half_length, y, 0),
                        (x+half_length, y+half_width, 0),
                        (x, y+half_width, 0)
                    ]

                    x += half_length + gap

                x = tx
                y += half_width + gap

                verts += [
                    (x, y, 0),
                    (x+length, y, 0),
                    (x+length, y+width, 0),
                    (x, y+width, 0)
                ]

                x += length + gap

                for _ in range(2):
                    verts += [
                        (x, y, 0),
                        (x + half_length, y, 0),
                        (x + half_length, y + half_width, 0),
                        (x, y + half_width, 0)
                    ]

                    y += half_width + gap

                p = len(verts)
                for i in range(p-24, p, 4):  # 6 faces, 4 vertices each
                    faces.append((i, i+3, i+2, i+1))

                x += half_length + gap
                y = ty

            y += half_width + width + (2*gap)

    @staticmethod
    def _hexagons(dims: tuple, props, verts, faces):
        side_length, gap = props.side_length, props.gap_uniform
        x_leg = side_length / 2
        y_leg = x_leg / tan(radians(30))
        d = y_leg / cos(radians(30))  # distance from center of hexagon to each vertex
        gap_dif = (gap / 2) * sqrt(3)

        # if we are doing dots, figure out the difference between the center and points, actual size is 2x values
        dot_x = d + (gap/2) - x_leg - gap_dif
        dot_y = ((2*y_leg) + gap - (2*gap_dif)) / 2

        start_y = y_leg
        upper_x, upper_y = dims[0] + d, dims[1] + (2*y_leg)
        while start_y < upper_y:
            move_down = True
            x = x_leg

            y = start_y
            while x < upper_x:
                verts += [
                    (x-x_leg, y-y_leg, 0),
                    (x+x_leg, y-y_leg, 0),
                    (x+d, y, 0),
                    (x+x_leg, y+y_leg, 0),
                    (x-x_leg, y+y_leg, 0),
                    (x-d, y, 0)
                ]

                p = len(verts) - 6
                faces.append((p, p+5, p+4, p+3, p+2, p+1))

                if props.with_dots:
                    # add cube dot
                    x += d + (gap/2)
                    y -= gap_dif

                    verts += [
                        (x, y, 0),
                        (x-dot_x, y-dot_y, 0),
                        (x, y-dot_y-dot_y, 0),
                        (x+dot_x, y-dot_y, 0),
                    ]

                    y += gap_dif
                    x += d + (gap / 2)

                    p = len(verts) - 4
                    faces.append((p, p+3, p+2, p+1))
                else:
                    x += x_leg + gap_dif + d
                    if move_down:
                        y -= y_leg + (gap / 2)
                    else:
                        y += y_leg + (gap / 2)

                    move_down = not move_down

            start_y += (2*y_leg) + gap

    @staticmethod
    def _octagons(dims: tuple, props, verts, faces):  # with dots since octagons cannot fit together otherwise
        side_length, gap = props.side_length, props.gap_uniform
        gap_dif = gap * cos(radians(30))
        x_leg = side_length / 2
        y_leg = x_leg / tan(radians(22.5))

        dot_s = ((2 * y_leg + gap) - 2*x_leg - 2*gap_dif) / 2

        y = y_leg
        upper_x, upper_y = dims[0] + y_leg, dims[1] + (2*y_leg)
        while y < upper_y:
            x = x_leg
            while x < upper_x:
                verts += [  # swapping x_leg with y_leg is on purpose
                    (x-x_leg, y-y_leg, 0),
                    (x+x_leg, y-y_leg, 0),
                    (x+y_leg, y-x_leg, 0),
                    (x+y_leg, y+x_leg, 0),

                    (x+x_leg, y+y_leg, 0),
                    (x-x_leg, y+y_leg, 0),
                    (x-y_leg, y+x_leg, 0),
                    (x-y_leg, y-x_leg, 0)
                ]

                p = len(verts) - 8
                faces.append((p, p+7, p+6, p+5, p+4, p+3, p+2, p+1))

                x += y_leg + (gap / 2)
                y -= x_leg + gap_dif

                verts += [
                    (x, y, 0),
                    (x-dot_s, y-dot_s, 0),
                    (x, y-dot_s-dot_s, 0),
                    (x+dot_s, y-dot_s, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += y_leg + (gap / 2)
                y += x_leg + gap_dif

            y += (2*y_leg) + gap

    @staticmethod
    def _corridor(dims: tuple, props, verts, faces):
        length, width, gap = props.tile_length, props.tile_width, props.gap_uniform
        half_width = props.alternating_row_width

        first_length_for_fixed_offset = length * (props.row_offset / 100)
        if first_length_for_fixed_offset == 0:
            first_length_for_fixed_offset = length

        offset_length_variance = JVFlooring._create_variance_function(props.vary_row_offset,
                                                                      length / 2,
                                                                      props.row_offset_variance)

        y = 0
        large = True
        upper_x, upper_y = dims
        while y < upper_y:
            x = 0

            if large:
                cur_width = width
            else:
                cur_width = half_width

            trimmed_width = min(cur_width, upper_y-y)
            while x < upper_x:
                cur_length = length

                if x == 0 and not large:
                    if props.vary_row_offset:
                        cur_length = offset_length_variance()
                    else:
                        cur_length = first_length_for_fixed_offset

                trimmed_length = min(cur_length, upper_x-x)

                verts += [
                    (x, y, 0),
                    (x+trimmed_length, y, 0),
                    (x+trimmed_length, y+trimmed_width, 0),
                    (x, y+trimmed_width, 0)
                ]

                p = len(verts) - 4
                faces.append((p, p+3, p+2, p+1))

                x += cur_length + gap

            large = not large
            y += cur_width + gap
