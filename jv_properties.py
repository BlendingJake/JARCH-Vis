from bpy.types import PropertyGroup
from bpy.props import PointerProperty, EnumProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty
from . jv_utils import Units
from . jv_types import get_object_type_handler


def jv_on_property_update(_, context):
    props = context.object.jv_properties

    if props is not None and props.update_automatically:
        handler = get_object_type_handler(props.object_type)

        if handler is not None:
            handler.update(props, context)


class JVProperties(PropertyGroup):
    object_type: EnumProperty(
        name="Type",
        items=(
            ("none", "None", ""),
            ("flooring", "Flooring", ""),
            ("siding", "Siding", ""),
            # ("roofing", "Roofing", ""),
            # ("stairs", "Stairs", ""),
            # ("window", "Window", "")
        ),
        default="none", description="The type of architecture to build", update=jv_on_property_update
    )

    update_automatically: BoolProperty(
        name="Update Automatically?",
        default=True, description="Update the mesh anytime a property is changed?", update=jv_on_property_update
    )

    # OBJECT STYLES ------------------------------------------------------------------------------
    flooring_pattern: EnumProperty(
        name="Pattern",
        items=(
            ("regular", "Regular", ""),  # wood-like
            ("checkerboard", "Checkerboard", ""),  # wood-like
            ("herringbone", "Herringbone", ""),  # wood-like
            ("chevron", "Chevron", ""),  # wood-like
            ("hopscotch", "Hopscotch", ""),  # tile-like
            ("windmill", "Windmill", ""),  # tile-like
            ("stepping_stone", "Stepping Stone", ""),  # tile-like
            ("hexagons", "Hexagons", ""),  # tile-like
            ("octagons", "Octagons", ""),  # tile-like
            ("corridor", "Cooridor", "")  # tile-like
        ), default="regular", description="Flooring Pattern", update=jv_on_property_update
    )

    siding_pattern: EnumProperty(
        name="Pattern",
        items=(
            ("regular", "Regular", ""),
        ), default="regular", description="Siding Pattern", update=jv_on_property_update
    )

    # OVERALL DIMENSIONS ------------------------------------------------------------------------
    length: FloatProperty(
        name="Total Length",
        min=0.5 * Units.FOOT, default=20 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="Total length of material", update=jv_on_property_update
    )

    width: FloatProperty(
        name="Total Width",
        min=0.5 * Units.FOOT, default=8 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="Total width of material", update=jv_on_property_update
    )

    height: FloatProperty(
        name="Total Height",
        min=1 * Units.FOOT, default=8 * Units.FOOT, precision=3, subtype="DISTANCE",
        description="Total height of the material", update=jv_on_property_update
    )

    # MATERIAL DIMENSIONS -----------------------------------------------------------------------
    board_width_wide: FloatProperty(
        name="Board Width",
        min=1 * Units.INCH, default=8 * Units.INCH,
        subtype="DISTANCE", description="The width of each board", update=jv_on_property_update
    )

    board_width_medium: FloatProperty(
        name="Board Width",
        min=1 * Units.INCH, default=6 * Units.INCH,
        subtype="DISTANCE", description="The width of each board", update=jv_on_property_update
    )

    board_width_narrow: FloatProperty(
        name="Board Width",
        min=1 * Units.INCH, default=3 * Units.INCH,
        subtype="DISTANCE", description="The width of each board", update=jv_on_property_update
    )

    vary_width: BoolProperty(
        name="Vary Width?",
        default=False, description="Vary the width of each board?", update=jv_on_property_update
    )

    width_variance: FloatProperty(
        name="Width Variance",
        min=1.00, max=100.00, default=25.00, subtype="PERCENTAGE",
        description="The width of each board will be in width +- width*variance", update=jv_on_property_update
    )

    board_length_long: FloatProperty(
        name="Board Length",
        min=1 * Units.FOOT, default=8 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="The length of each board", update=jv_on_property_update
    )

    board_length_medium: FloatProperty(
        name="Board Length",
        min=1 * Units.FOOT, default=4 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="The length of each board", update=jv_on_property_update
    )

    board_length_short: FloatProperty(
        name="Board Length",
        min=1 * Units.FOOT, default=2 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="The length of each board", update=jv_on_property_update
    )

    board_length_really_short: FloatProperty(
        name="Board Length",
        min=6 * Units.INCH, default=1 * Units.FOOT, precision=4,
        subtype="DISTANCE", description="The length of each board", update=jv_on_property_update
    )

    vary_length: BoolProperty(
        name="Vary Length?",
        default=False, description="Vary the length of each board?", update=jv_on_property_update
    )

    length_variance: FloatProperty(
        name="Length Variance",
        min=1.00, max=100.00, default=25.00, subtype="PERCENTAGE",
        description="The length of each board will be in length +- length*variance", update=jv_on_property_update
    )

    thickness: FloatProperty(
        name="Thickness",
        min=1 * Units.ETH_INCH, default=1 * Units.INCH, subtype="DISTANCE",
        description="The thickness of each board or tile", update=jv_on_property_update
    )

    vary_thickness: BoolProperty(
        name="Vary Thickness?",
        default=False, description="Vary the thickness of each board?", update=jv_on_property_update
    )

    thickness_variance: FloatProperty(
        name="Thickness Variance",
        min=1.00, max=100.00, default=25.00, subtype="PERCENTAGE",
        description="The thickness of each board will be in thickness +- thickness*variance",
        update=jv_on_property_update
    )

    gap_uniform: FloatProperty(
        name="Gap",
        min=0.00, default=1 * Units.STH_INCH, subtype="DISTANCE", step=1, precision=5,
        description="The gap around each board or tile", update=jv_on_property_update
    )

    # FLOORING SPECIFIC -------------------------------------------------------------------------
    gap_widthwise: FloatProperty(
        name="Gap Width-Wise",
        min=0.00, default=1 * Units.ETH_INCH, subtype="DISTANCE",
        description="The gap between each board width-wise", update=jv_on_property_update
    )

    gap_lengthwise: FloatProperty(
        name="Gap Length-Wise",
        min=0.00, default=1 * Units.ETH_INCH, subtype="DISTANCE",
        description="The gap between each board length-wise", update=jv_on_property_update
    )

    tile_width: FloatProperty(
        name="Tile Width",
        min=1 * Units.INCH, default=8 * Units.INCH, subtype="DISTANCE",
        description="The width of each tile", update=jv_on_property_update
    )

    tile_length: FloatProperty(
        name="Tile Length",
        min=1 * Units.INCH, default=8 * Units.INCH, subtype="DISTANCE",
        description="The length of each tile", update=jv_on_property_update
    )

    row_offset: FloatProperty(
        name="Row Offset",
        min=0.00, max=100.00, default=50.00, subtype="PERCENTAGE",
        description="How much alternating rows are offset", update=jv_on_property_update
    )

    vary_row_offset: BoolProperty(
        name="Vary Row Offset?",
        default=False, description="Vary the offset of each row?", update=jv_on_property_update
    )

    row_offset_variance: FloatProperty(
        name="Row Offset Variance",
        min=0.00, max=100.00, default=50.00, subtype="PERCENTAGE",
        description="Each row will be offset between (width / 2) * (1 - variance)", update=jv_on_property_update
    )

    checkerboard_board_count: IntProperty(
        name="Boards in Square",
        min=1, default=4, description="Number of boards in each square of checkerboard pattern",
        update=jv_on_property_update
    )

    with_dots: BoolProperty(
        name="With Dots?",
        default=True, description="Add cube between corners of hexagons?", update=jv_on_property_update
    )

    side_length: FloatProperty(
        name="Polygon Side Length",
        min=1 * Units.INCH, default=4 * Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The length of each side in the regular polygon", update=jv_on_property_update
    )

    alternating_row_width: FloatProperty(
        name="Alternating Row Width",
        min=1 * Units.INCH, default=3 * Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The width of the tiles in the alternating rows", update=jv_on_property_update
    )

    # SIDING SPECIFIC -------------------------------------------------------------------------
    siding_direction: EnumProperty(
        name="Siding Direction",
        items=(
            ("vertical", "Vertical", ""),
            ("horizontal", "Horizontal", "")
        ), default="vertical", description="Direction of siding", update=jv_on_property_update
    )

    slope_top: BoolProperty(
        name="Slope Top?",
        default=False, description="Cut a slope on the top of the siding?", update=jv_on_property_update
    )

    pitch: FloatProperty(
        name="Pitch X/12",
        default=4.00, min=0.00, step=1, precision=3,
        description="Pitch/Slope of the top of the siding, in rise/run format that is x/12",
        update=jv_on_property_update
    )

    pitch_offset: FloatVectorProperty(
        name="Offset of Slope",
        default=(0.0, 0.0, 0.0), size=3, precision=3, subtype="TRANSLATION",
        description="Offset from the top-center of the siding for the slope", update=jv_on_property_update
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
