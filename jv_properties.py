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
from math import radians
from bpy.types import PropertyGroup, Object
from bpy.props import PointerProperty, EnumProperty, FloatProperty, BoolProperty, IntProperty, FloatVectorProperty, \
    CollectionProperty, StringProperty
from . jv_utils import Units
from . jv_types import get_object_type_handler
import bpy


def jv_on_property_update(_, context):
    props = context.object.jv_properties

    if props is not None and props.update_automatically:
        converted = props.convert_source_object is not None
        handler = get_object_type_handler(props.object_type_converted if converted else props.object_type)
        handler.update(props, context)


def jv_on_face_group_index_update(_, context):
    props = context.object.jv_properties

    if 0 <= props.face_groups_index < len(props.face_groups):
        indices = set([int(i) for i in props.face_groups[props.face_groups_index].face_indices.split(",")])
        bpy.ops.object.editmode_toggle()

        # deselect everything before selecting the correct faces
        for vertex in context.object.data.vertices:
            vertex.select = False

        for edge in context.object.data.edges:
            edge.select = False

        for face in context.object.data.polygons:
            face.select = face.index in indices

        bpy.ops.object.editmode_toggle()


class BisectingPlane(PropertyGroup):
    normal: FloatVectorProperty(
        name="Normal", size=3, unit="LENGTH"
    )

    # LOCAL
    center: FloatVectorProperty(
        name="Center", size=3, unit="LENGTH"
    )


class FaceGroup(PropertyGroup):
    face_indices: StringProperty(
        name="Face Indices (CSV)", default=""
    )

    is_convex: BoolProperty(
        name="Convex?",
        description="Are the faces convex? Aka, are all interior angles <= 180 degrees and are there not cutouts?"
    )

    boolean_object: PointerProperty(
        name="Bolean Object", type=Object
    )

    # the rotation of the face group from the X-Y plane
    rotation: FloatVectorProperty(
        subtype="EULER", size=3
    )

    # LOCAL coordinate of bottom-left corner
    location: FloatVectorProperty(
        subtype="TRANSLATION", size=3
    )

    dimensions: FloatVectorProperty(
        unit="LENGTH", size=2
    )

    bisecting_planes: CollectionProperty(
        name="Bisecting Planes", type=BisectingPlane
    )


class Cutout(PropertyGroup):
    location: FloatVectorProperty(
        name="Location",
        default=(0.0, 0.0, 0.0), step=1, precision=3, subtype="TRANSLATION", size=3,
        description="The position of the lower-bottom-left corner", update=jv_on_property_update
    )

    rotation: FloatVectorProperty(
        name="Rotation",
        default=(0.0, 0.0, 0.0), step=2, precision=3, subtype="EULER", size=3,
        description="The rotation of the cutout", update=jv_on_property_update
    )

    dimensions: FloatVectorProperty(
        name="Dimensions",
        default=(Units.FOOT, Units.FOOT, Units.FOOT), step=1, precision=3, unit="LENGTH", size=3, min=0.0,
        description="The the dimensions of the cutout", update=jv_on_property_update
    )

    local: BoolProperty(
        name="Local Coordinates?", default=True,
        description="Are offset and rotation values in reference to the object's origin?",
        update=jv_on_property_update
    )


class JVProperties(PropertyGroup):
    object_type: EnumProperty(
        name="Type",
        items=(
            ("none", "None", ""),
            ("flooring", "Flooring", ""),
            ("siding", "Siding", ""),
            ("roofing", "Roofing", ""),
            ("windows", "Windows", "")
        ),
        default="none", description="The type of architecture to build", update=jv_on_property_update
    )

    object_type_converted: EnumProperty(
        name="Type",
        items=(
            ("none", "None", ""),
            ("flooring", "Flooring", ""),
            ("siding", "Siding", ""),
            ("roofing", "Roofing", "")
        ),
        default="none", description="The type of architecture to build", update=jv_on_property_update
    )

    update_automatically: BoolProperty(
        name="Update Automatically?",
        default=True, description="Update the mesh anytime a property is changed?", update=jv_on_property_update
    )

    convert_source_object: PointerProperty(
        name="Convert Source Object", type=Object
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
            ("dutch_lap", "Dutch Lap", ""),
            ("shiplap", "Shiplap", ""),
            ("clapboard", "Clapboard", ""),
            ("tin_regular", "Tin - Regular", ""),
            ("tin_angular", "Tin - Angular", ""),
            ("brick", "Brick", ""),
            ("shakes", "Shakes", ""),
            ("scallop_shakes", "Scallop Shakes", "")
        ), default="regular", description="Siding Pattern", update=jv_on_property_update
    )

    roofing_pattern: EnumProperty(
        name="Pattern",
        items=(
            ("tin_regular", "Tin - Regular", ""),
            ("tin_angular", "Tin - Angular", ""),
            ("tin_standing_seam", "Tin - Standing Seam", ""),
            ("shingles_3_tab", "Shingles - 3 Tab", ""),
            ("shingles_architectural", "Shingles - Architectural", ""),
            ("shakes", "Shakes", ""),
            ("terracotta", "Terracotta", "")
        ), default="tin_regular", description="Roofing Pattern", update=jv_on_property_update
    )

    window_pattern: EnumProperty(
        name="Pattern",
        items=(
            ("regular", "Regular", ""),
            ("arch", "Arch", ""),
            ("polygon", "Polygon", ""),
            ("gothic", "Gothic", ""),
            ("ellipse", "Ellipse", ""),
            ("circular", "Circular", ""),
            ("bow", "Bow", ""),
            ("bay", "Bay", "")
        ), default="regular", description="Window Pattern", update=jv_on_property_update
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

    # CUTOUTS -----------------------------------------------------------------------------------
    add_cutouts: BoolProperty(
        name="Cutouts?",
        description="Add box cutouts for things like windows or doors?", update=jv_on_property_update
    )

    cutouts: CollectionProperty(
        name="Cutouts", type=Cutout
    )

    # OBJECT STYLES ------------------------------------------------------------------------------
    face_groups: CollectionProperty(
        name="Face Groups", type=FaceGroup
    )

    face_groups_index: IntProperty(
        name="Face Groups Index", update=jv_on_face_group_index_update
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

    thickness_thin: FloatProperty(
        name="Thickness",
        min=Units.ETH_INCH, default=5*Units.STH_INCH, step=1, precision=4, subtype="DISTANCE",
        description="The thickness of each board, tile, shingle, etc.", update=jv_on_property_update
    )

    thickness: FloatProperty(
        name="Thickness",
        min=Units.ETH_INCH, default=1.5 * Units.INCH, step=1, subtype="DISTANCE",
        description="The thickness of each board, tile, shingle, etc.", update=jv_on_property_update
    )

    thickness_thick: FloatProperty(
        name="Thickness",
        min=1*Units.ETH_INCH, default=2.5*Units.INCH, step=1, precision=3, subtype="DISTANCE",
        description="The thickness of each board, tile, shingle, etc.", update=jv_on_property_update
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

    gap_widthwise: FloatProperty(
        name="Gap - Widthwise",
        min=0.00, default=Units.ETH_INCH, subtype="DISTANCE", step=1, precision=4,
        description="The gap between the board or tile in the width direction", update=jv_on_property_update
    )

    gap_lengthwise: FloatProperty(
        name="Gap - Lengthwise",
        min=0.00, default=Units.STH_INCH, subtype="DISTANCE", step=1, precision=4,
        description="The gap between the board or tile in the length direction", update=jv_on_property_update
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

    add_grout: BoolProperty(
        name="Add Grout?",
        default=True, description="Add cube for where the grout/mortar would be?", update=jv_on_property_update
    )

    grout_depth: FloatProperty(
        name="Grout Depth",
        min=0.00, max=100.00, default=5.00, precision=4, step=5, subtype="PERCENTAGE",
        description="The depth of the grout is depth*thickness", update=jv_on_property_update
    )

    shake_width: FloatProperty(
        name="Shake Width",
        min=1*Units.INCH, default=4*Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The width of each shake", update=jv_on_property_update
    )

    shake_length: FloatProperty(
        name="Shake Length",
        min=1*Units.INCH, default=6*Units.INCH, precision=4, step=2, subtype="DISTANCE",
        description="The length of each shake, the actual exposure will be length/2", update=jv_on_property_update
    )

    scallop_resolution: IntProperty(
        name="Curve Resolution",
        min=1, default=8, description="The smoothness of the curve", update=jv_on_property_update
    )

    pitch: FloatProperty(
        name="Pitch X/12",
        default=4.00, min=0.00, step=1, precision=3,
        description="Pitch/Slope of the top of the siding, in rise/run format that is x/12",
        update=jv_on_property_update
    )

    orientation: EnumProperty(
        name="Orientation",
        items=(
            ("vertical", "Vertical", ""),
            ("horizontal", "Horizontal", "")
        ), default="vertical", description="Orientation", update=jv_on_property_update
    )

    # FLOORING SPECIFIC -------------------------------------------------------------------------
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
        min=1 * Units.INCH, default=4 * Units.INCH, precision=4, step=2, subtype="DISTANCE",
        description="The length of each side in the regular polygon", update=jv_on_property_update
    )

    alternating_row_width: FloatProperty(
        name="Alternating Row Width",
        min=1 * Units.INCH, default=3 * Units.INCH, precision=4, step=2, subtype="DISTANCE",
        description="The width of the tiles in the alternating rows", update=jv_on_property_update
    )

    # SIDING SPECIFIC -------------------------------------------------------------------------
    slope_top: BoolProperty(
        name="Slope Top?",
        default=False, description="Cut a slope on the top of the siding?", update=jv_on_property_update
    )

    pitch_offset: FloatVectorProperty(
        name="Offset of Slope",
        default=(0.0, 0.0, 0.0), size=3, precision=3, subtype="TRANSLATION",
        description="Offset from the top-center of the siding for the slope", update=jv_on_property_update
    )

    dutch_lap_breakpoint: FloatProperty(
        name="Slope Breakpoint",
        default=65.00, min=5.00, max=95.00, precision=2, subtype="PERCENTAGE",
        description="The board will start sloping back at width*breakpoint up from the bottom",
        update=jv_on_property_update
    )

    battens: BoolProperty(
        name="Add Battens?",
        default=False, description="Add battens to the siding to cover the gaps between boards?",
        update=jv_on_property_update
    )

    batten_width: FloatProperty(
        name="Batten Width",
        default=2*Units.INCH, min=0.5*Units.INCH, subtype="DISTANCE",
        description="The width of the battens", update=jv_on_property_update
    )

    vary_batten_width: BoolProperty(
        name="Vary Batten Width?",
        default=False, description="Vary batten width?", update=jv_on_property_update
    )

    batten_width_variance: FloatProperty(
        name="Batten Width Variance",
        min=0.00, max=100.00, default=50.00, subtype="PERCENTAGE",
        description="Each batten's width will be in width +- (w * variance)", update=jv_on_property_update
    )

    brick_height: FloatProperty(
        name="Brick Width",
        min=1*Units.INCH, default=9*Units.Q_INCH, precision=4, step=1, subtype="DISTANCE",
        description="The height of each brick", update=jv_on_property_update
    )

    brick_length: FloatProperty(
        name="Brick Length",
        min=1*Units.INCH, default=8*Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The length of each brick", update=jv_on_property_update
    )

    joint_left: BoolProperty(
        name="Joint Left?",
        default=False, description="Leave 'thickness + gap' overhang on odd rows to allow jointing?",
        update=jv_on_property_update
    )

    joint_right: BoolProperty(
        name="Joint Right?",
        default=False, description="Leave 'thickness + gap' overhang on even rows to allow jointing?",
        update=jv_on_property_update
    )

    # ROOFING SPECIFIC -------------------------------------------------------------------------
    pan_width: FloatProperty(
        name="Pan Width",
        min=1*Units.INCH, default=Units.FOOT, precision=4, step=1, subtype="DISTANCE",
        description="The width of each pan", update=jv_on_property_update
    )

    terracotta_resolution: IntProperty(
        name="Curve Resolution",
        min=1, default=12, description="The resolution of the curve on the tile", update=jv_on_property_update
    )

    terracotta_radius: FloatProperty(
        name="Tile Radius",
        min=Units.INCH, default=2*Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The radius of the half-circle on the tile", update=jv_on_property_update
    )

    terracotta_gap: FloatProperty(
        name="Tile Gap",
        min=Units.H_INCH, default=1.5*Units.INCH, precision=4, step=1, subtype="DISTANCE",
        description="The distance between the half-circles on the tiles", update=jv_on_property_update
    )

    mirror: BoolProperty(
        name="Mirror?", default=False, description="Mirror roofing across X-axis?", update=jv_on_property_update
    )

    # WINDOW SPECIFIC --------------------------------------------------------------------------
    jamb_width: FloatProperty(
        name="Jamb Width",
        min=1 * Units.INCH, default=4 * Units.INCH, subtype="DISTANCE",
        description="The width of the jamb", update=jv_on_property_update
    )

    frame_width: FloatProperty(
        name="Frame Width",
        min=Units.ETH_INCH, default=1.5 * Units.INCH, subtype="DISTANCE",
        description="The width of the frame around the glass", update=jv_on_property_update
    )

    frame_thickness: FloatProperty(
        name="Frame Thickness",
        min=Units.H_INCH, default=Units.INCH, step=1, precision=3, subtype="DISTANCE",
        description="The thickness of the frame surrounding the glass pane", update=jv_on_property_update
    )

    window_width_medium: FloatProperty(
        name="Width",
        min=Units.FOOT, default=32 * Units.INCH, subtype="DISTANCE",
        description="The width of the windows", update=jv_on_property_update
    )

    window_width_wide: FloatProperty(
        name="Width",
        min=Units.FOOT, default=60 * Units.INCH, subtype="DISTANCE",
        description="The width of the windows", update=jv_on_property_update
    )

    window_width_extra_wide: FloatProperty(
        name="Width",
        min=Units.FOOT, default=6 * Units.FOOT, subtype="DISTANCE",
        description="The width of the windows", update=jv_on_property_update
    )

    window_height_tall: FloatProperty(
        name="Height",
        min=Units.FOOT, default=6 * Units.FOOT, subtype="DISTANCE",
        description="The height of the windows", update=jv_on_property_update
    )

    window_height_medium: FloatProperty(
        name="Height",
        min=Units.FOOT, default=4 * Units.FOOT, subtype="DISTANCE",
        description="The height of the gliding windows", update=jv_on_property_update
    )

    window_height_short: FloatProperty(
        name="Height",
        min=Units.FOOT, default=3 * Units.FOOT, subtype="DISTANCE",
        description="The height of the gliding windows", update=jv_on_property_update
    )

    num_joined_windows: IntProperty(
        name="Window Gang Count",
        min=1, default=1, update=jv_on_property_update
    )

    window_radius: FloatProperty(
        name="Radius",
        min=Units.FOOT, default=1.5 * Units.FOOT, subtype="DISTANCE",
        description="The radius of the window", update=jv_on_property_update
    )

    window_side_count: IntProperty(
        name="Sides",
        min=3, default=3, update=jv_on_property_update
    )

    full_circle: BoolProperty(
        name="Full Circle?",
        default=True, update=jv_on_property_update
    )

    window_angle: FloatProperty(
        name="Angle",
        unit="ROTATION", min=radians(15), default=radians(90), update=jv_on_property_update
    )

    window_roundness: FloatProperty(
        name="Roundness",
        max=100.0, min=1.0, default=25.0, subtype="PERCENTAGE", update=jv_on_property_update,
        description="The ellipse's height will be (width / 2) * roundness. A value of 100% will form a half-circle"
    )

    window_resolution: IntProperty(
        name="Resolution",
        min=10, default=64, step=2, update=jv_on_property_update
    )

    slider: BoolProperty(
        name="Slider?",
        default=True, update=jv_on_property_update
    )

    bay_angle: FloatProperty(
        name="Side Pane Angle",
        min=radians(10), max=radians(90), default=radians(45), subtype="ANGLE", update=jv_on_property_update
    )

    window_depth: FloatProperty(
        name="Window Depth",
        min=Units.FOOT, default=2 * Units.FOOT, subtype="DISTANCE", update=jv_on_property_update
    )

    bow_segments: IntProperty(
        name="Segments",
        min=2, default=5, update=jv_on_property_update
    )


def register():
    from bpy.utils import register_class
    from bpy.types import Object

    register_class(BisectingPlane)
    register_class(Cutout)
    register_class(FaceGroup)
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
    unregister_class(FaceGroup)
    unregister_class(Cutout)
    unregister_class(BisectingPlane)


if __name__ == "__main__":
    register()
