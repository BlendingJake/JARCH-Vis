from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty, EnumProperty


class JVProperties(PropertyGroup):
    object_type: StringProperty()

    flooring_style: EnumProperty(
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


def register():
    from bpy.utils import register_class
    from bpy.types import Object

    register_class(JVProperties)
    Object.jv_properties = PointerProperty(
        type=JVProperties,
        name="jv_properties",
        description="All possible properties for any JARCH Vis object"
    )


def unregister():
    from bpy.utils import unregister_class
    from bpy.types import Object

    del Object.jv_properties
    unregister_class(JVProperties)


if __name__ == "__main__":
    register()
