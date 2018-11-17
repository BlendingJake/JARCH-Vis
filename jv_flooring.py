from jv_base import JVBase
from bpy.props import EnumProperty


class JVFlooring(JVBase):
    def __init__(self, obj, is_converted=False):
        super(JVFlooring, self).__init__(obj, is_converted)

        self.flooring_style = EnumProperty(
            items=(
                ("wood_regular", "Wood - Regular", ""),
                ("parquet", "Parquet", ""),
                ("herringbone_parquet", "Herringbone Parquet", ""),
                ("herringbone", "Herringbone", ""),
                ("tile_regular", "Tile - Regular", ""),
                ("tile_large_small", "Tile - Large + Small", ""),
                ("tile_large_many_small", "Tile - Large + Many Small", ""),
                ("hexagons", "Hexagons", "")
            ),
            default="wood_regular", description="Flooring Pattern/Style", name="Flooring Style"
        )
        self.over_width = self.build_general_property("over_width")

    def draw(self, layout):
        layout.prop(self, "flooring_style", icon="OBJECT_DATA")
