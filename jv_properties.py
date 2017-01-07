import bpy
from bpy.props import FloatProperty, IntProperty, EnumProperty, StringProperty, BoolProperty, FloatVectorProperty
from . jv_utils import METRIC_INCH, METRIC_FOOT, delete_materials, preview_materials
from . jv_flooring import update_flooring
from . jv_roofing import update_roofing, update_selection
from . jv_siding import update_siding
from . jv_stairs import update_stairs
from . jv_windows import update_window
from math import radians


def jv_update_object(self, context):
    o = context.object
    updates = {"flooring": update_flooring, "siding": update_siding, "roofing": update_roofing, "stair": update_stairs,
               "window": update_window}

    if o.jv_internal_type in updates:
        updates[o.jv_internal_type](self, context)

tp = bpy.types.Object

tp.jv_internal_type = StringProperty()
# general variables
tp.jv_w_types = EnumProperty(items=(("1", "Double-Hung", ""), ("2", "Gliding", ""),
                                                  ("3", "Stationary", ""), ("4", "Odd-Shaped", ""),
                                                  ("5", "Bay/Bow", "")), name="", update=jv_update_object)
tp.jv_odd_types = EnumProperty(items=(("1", "Polygon", ""), ("2", "Circular", ""), ("3", "Arch", ""),
                                                    ("4", "Gothic", ""), ("5", "Oval", "")), name="",
                                             update=jv_update_object)
tp.jv_object_add = StringProperty(default="none", update=jv_update_object)
tp.jv_jamb_width = FloatProperty(name="Jamb Width", subtype="DISTANCE", min=2 / METRIC_INCH,
                                               max=8 / METRIC_INCH, default=4 / METRIC_INCH, update=jv_update_object)

# double hung
tp.jv_dh_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=3 / METRIC_FOOT,
                                             default=32 / METRIC_INCH, update=jv_update_object)
tp.jv_dh_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                              max=6 / METRIC_FOOT, default=48 / METRIC_INCH, update=jv_update_object)
tp.jv_dh_num = IntProperty(name="Number Ganged Together", min=1, max=4, default=1,
                                         update=jv_update_object)
# gliding
tp.jv_gl_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=6 / METRIC_FOOT,
                                             default=60 / METRIC_INCH, update=jv_update_object)
tp.jv_gl_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                              max=4 / METRIC_FOOT, default=36 / METRIC_INCH, update=jv_update_object)
tp.jv_gl_slide_right = BoolProperty(name="Slide Right?", default=True, update=jv_update_object)
# stationary & odd-shaped
tp.jv_so_width = FloatProperty(name="Width", subtype="DISTANCE", min=1 / METRIC_FOOT, max=6 / METRIC_FOOT,
                                             default=24 / METRIC_INCH, update=jv_update_object)
tp.jv_so_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                              max=10 / METRIC_FOOT, default=36 / METRIC_INCH, update=jv_update_object)
tp.jv_so_height_tall = FloatProperty(name="Height", subtype="DISTANCE", min=3 / METRIC_FOOT,
                                                   max=20 / METRIC_FOOT, default=5 / METRIC_FOOT,
                                                   update=jv_update_object)
tp.jv_o_radius = FloatProperty(name="Radius", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                             max=3 / METRIC_FOOT, default=1.5 / METRIC_FOOT, update=jv_update_object)
# polygon
tp.jv_sides = IntProperty(name="Sides", min=3, max=12, default=3, update=jv_update_object)
# circular
tp.jv_full_circle = BoolProperty(name="Full Circle?", default=True, update=jv_update_object)
tp.jv_w_angle = FloatProperty(name="Angle", unit="ROTATION", min=radians(45), max=radians(270),
                                            default=radians(90), update=jv_update_object)
# arch
tp.jv_roundness = FloatProperty(name="Roundness", subtype="PERCENTAGE", max=100.0, min=1.0, default=25.0,
                                              update=jv_update_object)
tp.jv_resolution = IntProperty(name="Resolution", min=32, max=512, default=64, step=2,
                                             update=jv_update_object)
tp.jv_is_slider = BoolProperty(name="Slider?", update=jv_update_object)
# bay
tp.jv_ba_width = FloatProperty(name="Width", subtype="DISTANCE", min=2 / METRIC_FOOT,
                                             max=20 / METRIC_FOOT, default=72 / METRIC_INCH, update=jv_update_object)
tp.jv_ba_height = FloatProperty(name="Height", subtype="DISTANCE", min=1 / METRIC_FOOT,
                                              max=15 / METRIC_FOOT, default=48 / METRIC_INCH, update=jv_update_object)
tp.jv_is_bay = BoolProperty(name="Bay?", default=True, update=jv_update_object)
tp.jv_bay_angle = FloatProperty(name="Side Pane Angle", subtype="ANGLE", min=radians(10), max=radians(75),
                                              default=radians(45), update=jv_update_object)
tp.jv_depth = FloatProperty(name="Window Depth", subtype="DISTANCE", min=12/METRIC_INCH,
                                          max=4/METRIC_FOOT, default=2/METRIC_FOOT, update=jv_update_object)
tp.jv_bow_segments = EnumProperty(items=(("2", "2", ""), ("4", "4", ""), ("6", "6", ""), ("8", "8", ""),
                                                       ("10", "10", ""), ("12", "12", ""), ("14", "14", "")),
                                                name="Segments", update=jv_update_object)
tp.jv_is_split_center = BoolProperty(name="Split Center Pane?", default=False, update=jv_update_object)
tp.jv_is_double_hung = BoolProperty(name="Double Hung?", default=True, update=jv_update_object)

tp.jv_object_add = StringProperty(default="none", update=jv_update_object)
tp.jv_cut_name = StringProperty(default="none")
tp.jv_is_cut = StringProperty(default="none")
# type/material
tp.jv_mat = EnumProperty(items=(("1", "Wood", ""), ("2", "Tile", "")), default="1", description="Material",
                         update=jv_update_object, name="")
tp.jv_wood_types = EnumProperty(items=(("1", "Regular", ""), ("2", "Parquet", ""), ("3", "Herringbone Parquet", ""),
                                       ("4", "Herringbone", "")), default="1", description="Wood Type",
                                update=jv_update_object, name="")
tp.jv_tile_types = EnumProperty(items=(("1", "Regular", ""), ("2", "Large + Small", ""), ("3", "Large + Many Small", ""),
                                       ("4", "Hexagonal", "")), default="1", description="Tile Type",
                                update=jv_update_object, name="")
# measurements
tp.jv_over_width = FloatProperty(name="Overall Width", min=2.00 / METRIC_FOOT, max=100.00 / METRIC_FOOT,
                                 default=8.00 / METRIC_FOOT, subtype="DISTANCE", description="Overall Width",
                                 update=jv_update_object)
tp.jv_over_length = FloatProperty(name="Overall Length", min=2.0 / METRIC_FOOT, max=100.00 / METRIC_FOOT,
                                  default=8.00 / METRIC_FOOT, subtype="DISTANCE", description="Overall Length",
                                  update=jv_update_object)
tp.jv_b_width = FloatProperty(name="Board Width", min=2.00 / METRIC_INCH, max=14.00 / METRIC_INCH,
                              default=6.00 / METRIC_INCH, subtype="DISTANCE", description="Board Width",
                              update=jv_update_object)
tp.jv_b_length = FloatProperty(name="Board Length", min=4.00 / METRIC_FOOT, max=20.00 / METRIC_FOOT,
                               default=8.00 / METRIC_FOOT, subtype="DISTANCE", description="Board Length",
                               update=jv_update_object)
tp.jv_b_length_s = FloatProperty(name="Board Length", min=1.00 / METRIC_FOOT, max=4.00 / METRIC_FOOT,
                                 default=1.5 / METRIC_FOOT, subtype="DISTANCE", description="Board Length",
                                 update=jv_update_object)
tp.jv_hb_direction = EnumProperty(items=(("1", "Forwards (+y)", ""), ("2", "Backwards (-y)", ""),
                                         ("3", "Right (+x)", ""), ("4", "Left (-x)", "")), name="Direction",
                                  description="Herringbone Direction", update=jv_update_object)
tp.jv_thickness = FloatProperty(name="Floor Thickness", min=0.75 / METRIC_INCH, max=1.5 / METRIC_INCH,
                                default=1 / METRIC_INCH, subtype="DISTANCE", description="Thickness Of Flooring",
                                update=jv_update_object)
tp.jv_is_length_vary = BoolProperty(name="Vary Length?", default=False, description="Vary Lengths?",
                                    update=jv_update_object)
tp.jv_length_vary = FloatProperty(name="Length Variance", min=1.00, max=100.0, default=50.0, subtype="PERCENTAGE",
                                  description="Length Variance", update=jv_update_object)
tp.jv_max_boards = IntProperty(name="Max # Of Boards", min=2, max=10, default=2,
                               description="Maximum Number Of Boards Possible In One Length", update=jv_update_object)
tp.jv_is_width_vary = BoolProperty(name="Vary Width?", default=False, description="Vary Widths?", update=jv_update_object)
tp.jv_width_vary = FloatProperty(name="Width Variance", min=1.00, max=100.0, default=50.0, subtype="PERCENTAGE",
                                 description="Width Variance", update=jv_update_object)
tp.jv_num_boards = IntProperty(name="# Of Boards", min=2, max=6, default=4, description="Number Of Boards In Square",
                               update=jv_update_object)
tp.jv_space_l = FloatProperty(name="Length Spacing", min=0.001 / METRIC_INCH, max=0.5 / METRIC_INCH,
                              default=0.125 / METRIC_INCH, subtype="DISTANCE",
                              description="Space Between Boards Length Ways", update=jv_update_object)
tp.jv_space_w = FloatProperty(name="Width Spacing", min=0.001 / METRIC_INCH, max=0.5 / METRIC_INCH,
                              default=0.125 / METRIC_INCH, subtype="DISTANCE",
                              description="Space Between Boards Width Ways", update=jv_update_object)
tp.jv_spacing = FloatProperty(name="Spacing", min=0.001 / METRIC_INCH, max=1.0 / METRIC_INCH,
                              default=0.25 / METRIC_INCH, subtype="DISTANCE", description="Space Between Tiles/Boards",
                              update=jv_update_object)
tp.jv_is_bevel = BoolProperty(name="Bevel?", default=False, update=jv_update_object)
tp.jv_res = IntProperty(name="Bevel Resolution", min=1, max=5, default=1, update=jv_update_object)
tp.jv_bevel_amo = FloatProperty(name="Bevel Amount", min=0.001 / METRIC_INCH, max=0.5 / METRIC_INCH,
                                default=0.15 / METRIC_INCH, subtype="DISTANCE", description="Bevel Amount",
                                update=jv_update_object)
tp.jv_is_ran_thickness = BoolProperty(name="Random Thickness?", default=False, update=jv_update_object)
tp.jv_ran_thickness = FloatProperty(name="Thickness Variance", min=0.1, max=100.0, default=50.0, subtype="PERCENTAGE",
                                    update=jv_update_object)
# tile specific
tp.jv_t_width = FloatProperty(name="Tile Width", min=2.00 / METRIC_INCH, max=24.00 / METRIC_INCH,
                              default=8.00 / METRIC_INCH, subtype="DISTANCE", description="Tile Width",
                              update=jv_update_object)
tp.jv_t_length = FloatProperty(name="Tile Length", min=2.00 / METRIC_INCH, max=24.00 / METRIC_INCH,
                               default=8.00 / METRIC_INCH, subtype="DISTANCE", description="Tile Length",
                               update=jv_update_object)
tp.jv_grout_depth = FloatProperty(name="Grout Depth", min=0.01 / METRIC_INCH, max=0.40 / 39.701,
                                  default=0.10 / METRIC_INCH, subtype="DISTANCE", description="Grout Depth",
                                  update=jv_update_object)
tp.jv_is_offset = BoolProperty(name="Offset Tiles?", default=False, description="Offset Tile Rows",
                               update=jv_update_object)
tp.jv_offset = FloatProperty(name="Offset", min=0.001, max=100.0, default=50.0, subtype="PERCENTAGE",
                             description="Tile Offset Amount", update=jv_update_object)
tp.jv_is_random_offset = BoolProperty(name="Random Offset?", default=False, description="Offset Tile Rows Randomly",
                                      update=jv_update_object)
tp.jv_offset_vary = FloatProperty(name="Offset Variance", min=0.001, max=100.0, default=50.0, subtype="PERCENTAGE",
                                  description="Offset Variance", update=jv_update_object)
tp.jv_t_width_s = FloatProperty(name="Small Tile Width", min=2.00 / METRIC_INCH, max=10.00 / METRIC_INCH,
                                default=6.00 / METRIC_INCH, subtype="DISTANCE", description="Small Tile Width",
                                update=jv_update_object)
# materials
tp.jv_is_material = BoolProperty(name="Cycles Materials?", default=False, description="Adds Cycles Materials",
                                 update=delete_materials)
tp.jv_is_preview = BoolProperty(name="Preview Material?", default=False, description="Preview Material On Object",
                                update=preview_materials)
tp.jv_im_scale = FloatProperty(name="Image Scale", max=10.0, min=0.1, default=1.0, description="Change Image Scaling")
tp.jv_col_image = StringProperty(name="", subtype="FILE_PATH", description="File Path For Color Image")
tp.jv_is_bump = BoolProperty(name="Normal Map?", default=False, description="Add Normal To Material?")
tp.jv_norm_image = StringProperty(name="", subtype="FILE_PATH", description="File Path For Normal Map Image")
tp.jv_bump_amo = FloatProperty(name="Normal Strength", min=0.001, max=2.000, default=0.250,
                               description="Normal Map Strength")
tp.jv_is_unwrap = BoolProperty(name="UV Unwrap?", default=True, description="UV Unwraps Siding", update=unwrap_flooring)
tp.jv_mortar_color = FloatVectorProperty(name="Mortar Color", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                         max=1.0, description="Color For Mortar")
tp.jv_mortar_bump = FloatProperty(name="Mortar Bump", min=0.0, max=1.0, default=0.25, description="Mortar Bump Amount")
tp.jv_is_rotate = BoolProperty(name="Rotate Image?", default=False, description="Rotate Image 90 Degrees")
tp.jv_is_random_uv = BoolProperty(name="Random UV's?", default=True, description="Random UV's", update=jv_update_object)

tp.jv_face_group_ct = IntProperty(default=0)
tp.jv_group_index = IntProperty(default=0, update=update_selection)

# planes info
tp.jv_pl_z_rot = FloatProperty(unit="ROTATION", name="Object Z Rotation")
tp.jv_pl_pitch = FloatProperty(min=1.0, max=24.0, default=4.0, name="Pitch X/12")

# overall
tp.jv_main_name = StringProperty(default="none")
tp.jv_object_add = StringProperty(default="none", update=jv_update_object)
tp.jv_roof_types = EnumProperty(name="Material", items=(("1", "Tin", ""), ("2", "Shingles", ""),
                                                               ("3", "Terra Cotta", "")), update=jv_update_object)
tp.jv_shingle_types = EnumProperty(name="Shingle Style", items=(("1", "Architectural", ""),
                                                                         ("2", "3-Tab", "")), update=jv_update_object)
tp.jv_tin_types = EnumProperty(name="Tin Type", items=(("1", "Normal", ""), ("2", "Angular", ""),
                                                               ("3", "Standing Seam", "")), update=jv_update_object)
tp.jv_slope = FloatProperty(name="Slope (X/12)", min=1.0, max=12.0, default=4.0, update=jv_update_object)
tp.jv_is_mirrored = BoolProperty(name="Mirror?", default=True, update=jv_update_object)

tp.jv_terra_cotta_res = IntProperty(name="Curve Resolution", min=3, max=10, default=5, update=jv_update_object)
tp.jv_tile_radius = FloatProperty(name="Tile Radius", min=1.5 / METRIC_INCH, max=3.0 / METRIC_INCH,
                                                default=2.0 / METRIC_INCH, update=jv_update_object, subtype="DISTANCE")

# materials
tp.jv_tin_color = FloatVectorProperty(name="Tin Color", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                max=1.0, description="Color For Tin")

tp.jv_siding_types = EnumProperty(items=(("1", "Wood", ""), ("2", "Vinyl", ""), ("3", "Tin", ""),
                                           ("4", "Fiber Cement", ""), ("5", "Bricks", ""), ("6", "Stone", "")),
                                    default="1", name="", update=update_siding)
tp.tin_types = EnumProperty(items=(("1", "Normal", ""), ("2", "Angular", "")), default="1",
                                          name="", update=update_siding)
tp.wood_types = EnumProperty(items=(("1", "Vertical", ""), ("2", "Vertical: Tongue & Groove", ""),
                                                  ("3", "Vertical: Board & Batten", ""), ("4", "Horizontal: Lap", ""),
                                                  ("5", "Horizontal: Lap Bevel", "")), default="1", name="",
                                           update=update_siding)
tp.vinyl_types = EnumProperty(items=(("1", "Vertical", ""), ("2", "Horizontal: Lap", ""),
                                                   ("3", "Horizontal: Dutch Lap", "")), default="1", name="",
                                            update=update_siding)
# measurements
tp.jv_pre_jv_dims = StringProperty(default="none")
tp.jv_previous_rotation = StringProperty(default="none")
tp.jv_dims = StringProperty(default="none")
tp.jv_is_slope = BoolProperty(name="Slope Top?", default=False, update=update_siding)
tp.jv_over_height = FloatProperty(name="Overall Height", min=0.30486, max=15.2399, default=2.4384,
                                             subtype="DISTANCE", description="Height", update=update_siding)
tp.jv_over_width = FloatProperty(name="Overall Width", min=0.609, max=30.4799, default=6.0959,
                                            subtype="DISTANCE", description="Width From Left To Right",
                                            update=update_siding)
tp.jv_batten_width = FloatProperty(name="Batten Width", min=0.5 / METRIC_INCH, max=4 / METRIC_INCH,
                                              default=2 / METRIC_INCH, subtype="DISTANCE",
                                              description="Width Of Batten", update=update_siding)
tp.jv_slope = FloatProperty(name="Slope (X/12)", min=1.0, max=12.0, default=4.0,
                                       description="Slope In RISE/RUN Format In Inches", update=update_siding)
tp.jv_is_cutout = BoolProperty(name="Cutouts?", default=False, description="Cut Rectangles Out (Slower)",
                                          update=update_siding)
tp.jv_num_cutouts = IntProperty(name="# Cutouts", min=1, max=6, default=1, update=update_siding)
tp.jv_is_screws = BoolProperty(name="Screw Heads?", default=False, description="Add Screw Heads?",
                                          update=update_siding)
tp.jv_bevel_width = FloatProperty(name="Bevel Width", min=0.05 / METRIC_INCH, max=0.5 / METRIC_INCH,
                                             default=0.2 / METRIC_INCH, subtype="DISTANCE", update=update_siding)
tp.jv_x_offset = FloatProperty(name="X-Offset", min=-2.0 / METRIC_INCH, max=2.0 / METRIC_INCH, default=0.0,
                                          subtype="DISTANCE", update=update_siding)
# brick
tp.jv_br_width = FloatProperty(name="Brick Width", min=4.0 / METRIC_INCH, max=10.0 / METRIC_INCH,
                                         default=7.625 / METRIC_INCH, subtype="DISTANCE", description="Brick Width",
                                         update=update_siding)
tp.jv_br_height = FloatProperty(name="Brick Height", min=2.0 / METRIC_INCH, max=5.0 / METRIC_INCH,
                                          default=2.375 / METRIC_INCH, subtype="DISTANCE", description="Brick Height",
                                          update=update_siding)
tp.jv_br_ran_offset = BoolProperty(name="Random Offset?", default=False,
                                             description="Random Offset Between Rows", update=update_siding)
tp.jv_br_offset = FloatProperty(name="Brick Offset", subtype="PERCENTAGE", min=0, max=100.0, default=50.0,
                                          description="Brick Offset Between Rows", update=update_siding)
tp.jv_br_gap = FloatProperty(name="Gap", min=0.1 / METRIC_INCH, max=1 / METRIC_INCH,
                                       default=0.5 / METRIC_INCH, subtype="DISTANCE", description="Gap Between Bricks",
                                       update=update_siding)
tp.jv_br_m_depth = FloatProperty(name="Mortar Depth", min=0.1 / METRIC_INCH, max=1.0 / METRIC_INCH,
                                         default=0.25 / METRIC_INCH, subtype="DISTANCE", description="Mortar Depth",
                                         update=update_siding)
tp.jv_br_vary = FloatProperty(name="Offset Varience", subtype="PERCENTAGE", min=0, max=100, default=50,
                                        description="Offset Varience", update=update_siding)
tp.jv_bump_type = EnumProperty(items=(("1", "Dimpled", ""), ("2", "Ridges", ""), ("3", "Flaky", ""),
                                                 ("4", "Smooth", "")), name="Bump Type")
tp.jv_color_style = EnumProperty(items=(("constant", "Constant", "Single Color"),
                                                   ("speckled", "Speckled", "Speckled Pattern"),
                                                   ("multiple", "Multiple", "Two Mixed Colors"),
                                                   ("extreme", "Extreme", "Three Mixed Colors")), name="Color Style")
tp.jv_color2 = FloatVectorProperty(name="Color 2", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                  max=1.0, description="Color 2 For Siding")
tp.jv_color3 = FloatVectorProperty(name="Color 3", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                  max=1.0, description="Color 3 For Siding")
tp.jv_color_sharp = FloatProperty(name="Color Sharpness", min=0.0, max=10.0, default=1.0,
                                             description="Sharpness Of Color Edges")
tp.jv_mortar_color = FloatVectorProperty(name="Mortar Color", subtype="COLOR", default=(1.0, 1.0, 1.0),
                                                    min=0.0, max=1.0, description="Color For Mortar")
tp.jv_mortar_bump = FloatProperty(name="Mortar Bump", min=0.0, max=1.0, default=0.25,
                                             description="Mortar Bump Amount")
tp.jv_brick_bump = FloatProperty(name="Brick Bump", min=0.0, max=1.0, default=0.25,
                                            description="Brick Bump Amount")
tp.jv_color_scale = FloatProperty(name="Color Scale", min=0.01, max=20.0, default=1.0,
                                             description="Color Scale")
tp.jv_bump_scale = FloatProperty(name="Bump Scale", min=0.01, max=20.0, default=1.0,
                                            description="Bump Scale")
tp.jv_is_corner = BoolProperty(name="Usable Corners?", default=False,
                                          description="Alternate Ends To Allow Corners", update=update_siding)
tp.jv_is_invert = BoolProperty(name="Flip Rows?", default=False, description="Flip Offset Staggering",
                                          update=update_siding)
tp.jv_is_soldier = BoolProperty(name="Soldier Bricks?", default=False, description="Bricks Above Cutouts",
                                           update=update_siding)
tp.jv_is_left = BoolProperty(name="Corners Left?", default=True, description="Usable Corners On Left",
                                        update=update_siding)
tp.jv_is_right = BoolProperty(name="Corners Right?", default=True, description="Usable Corners On Right",
                                         update=update_siding)
# stone
tp.jv_av_width = FloatProperty(name="Average Width", default=10.00 / METRIC_INCH, min=4.00 / METRIC_INCH,
                                          max=36.00 / METRIC_INCH, subtype="DISTANCE",
                                          description="Average Width Of Stones", update=update_siding)
tp.jv_av_height = FloatProperty(name="Average Height", default=6.00 / METRIC_INCH, min=2.00 / METRIC_INCH,
                                           max=36.00 / METRIC_INCH, subtype="DISTANCE",
                                           description="Average Height Of Stones", update=update_siding)
tp.jv_random_size = FloatProperty(name="Size Randomness", default=25.00, max=100.00, min=0.00,
                                          subtype="PERCENTAGE", description="Size Randomness", update=update_siding)
tp.jv_random_bump = FloatProperty(name="Bump Randomness", default=25.00, max=100.00, min=0.00,
                                          subtype="PERCENTAGE", description="Bump Randomness", update=update_siding)
tp.jv_st_m_depth = FloatProperty(name="Mortar Depth", default=1.5 / METRIC_INCH, min=0.5 / METRIC_INCH,
                                          max=3.0 / METRIC_INCH, subtype="DISTANCE", description="Depth Of Mortar",
                                          update=update_siding)
tp.jv_sb_mat_type = EnumProperty(name="", items=(("1", "Image", ""), ("2", "Procedural", "")), default="1",
                                      description="Stone Material Type")
# materials
tp.jv_rgba_color = FloatVectorProperty(name="Color", subtype="COLOR", default=(1.0, 1.0, 1.0), min=0.0,
                                                 max=1.0, description="Color For Siding")
# cutout variables
desc = "X, Y, Height, Width In (ft/m)"
tp.jv_nc1 = StringProperty(name="", default="", description=desc, update=update_siding)
tp.jv_nc2 = StringProperty(name="", default="", description=desc, update=update_siding)
tp.jv_nc3 = StringProperty(name="", default="", description=desc, update=update_siding)
tp.jv_nc4 = StringProperty(name="", default="", description=desc, update=update_siding)
tp.jv_nc5 = StringProperty(name="", default="", description=desc, update=update_siding)
tp.jv_nc6 = StringProperty(name="", default="", description=desc, update=update_siding)

tp.jv_stair_style = EnumProperty(items=(("1", "Normal", ""), ("2", "Winding", ""), ("3", "Spiral", "")),
                                        default="1", description="Stair Style", update=update_stairs, name="")
tp.jv_overhang_style = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                  ("4", "Both", "")), default="1", description="Overhang Style",
                                           update=update_stairs, name="")
# common variables
tp.jv_num_steps = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
tp.jv_num_steps2 = IntProperty(name="Number Of Steps", min=1, max=48, default=13, update=update_stairs)
tp.jv_tread_width = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                               default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_riser_height = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_over_front = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                              default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_over_sides = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                              default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_stair_width = FloatProperty(name="Stair Width", min=36.0 / METRIC_INCH, max=60.0 / METRIC_INCH,
                                         default=40.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_is_riser = BoolProperty(name="Risers?", default=True, update=update_stairs)
tp.jv_is_custom_tread = BoolProperty(name="Custom Treads?", default=False, update=update_stairs)
tp.jv_custom_treads = StringProperty(name="Custom Tread", default="", update=update_stairs)
# normal style
tp.jv_num_landings = IntProperty(name="Number Of Landings", min=0, max=2, default=0, update=update_stairs)
tp.jv_is_close_sides = BoolProperty(name="Close Sides?", default=False, update=update_stairs)
tp.jv_set_steps_in = BoolProperty(name="Set Steps In?", default=False, update=update_stairs)
tp.jv_is_landing = BoolProperty(name="Create Landings?", default=True, update=update_stairs)
tp.jv_is_light = BoolProperty(name="Allow Recessed Lights?", default=False, update=update_stairs,
                                           description="Space Middle Step Jacks To Allow Recessed Lights")
# landing 0
tp.jv_num_steps0 = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
tp.jv_tread_width0 = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                                default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_riser_height0 = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                 default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_landing_depth = FloatProperty(name="Landing 1 Depth", min=36 / METRIC_INCH, max=60 / METRIC_INCH,
                                                  default=40 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_landing_rot0 = EnumProperty(items=(("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")),
                                               update=update_stairs, name="")
tp.jv_over_front0 = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_over_sides0 = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_overhang_style0 = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                   ("4", "Both", "")), default="1", description="Overhang Style",
                                            update=update_stairs, name="")
tp.jv_is_backwards0 = BoolProperty(name="Turn Backwards?", default=False, update=update_stairs)
# landing 1
tp.jv_num_steps1 = IntProperty(name="Number Of Steps", min=1, max=24, default=13, update=update_stairs)
tp.jv_landing_rot1 = EnumProperty(items=(("1", "Forwards", ""), ("2", "Left", ""), ("3", "Right", "")),
                                               update=update_stairs, name="")
tp.jv_tread_width1 = FloatProperty(name="Tread Width", min=9.0 / METRIC_INCH, max=16.0 / METRIC_INCH,
                                                default=9.5 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_riser_height1 = FloatProperty(name="Riser Height", min=5.0 / METRIC_INCH, max=8.0 / METRIC_INCH,
                                                 default=7.4 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.s_landing_depth1 = FloatProperty(name="Landing 2 Depth", min=36 / METRIC_INCH, max=60 / METRIC_INCH,
                                                  default=40 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_over_front1 = FloatProperty(name="Front Overhang", min=0.0, max=1.25 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_over_sides1 = FloatProperty(name="Side Overhang", min=0.0, max=2.0 / METRIC_INCH,
                                               default=1.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_overhang_style1 = EnumProperty(items=(("1", "Normal", ""), ("2", "Right", ""), ("3", "Left", ""),
                                                   ("4", "Both", "")), default="1", description="Overhang Style",
                                            update=update_stairs, name="")
tp.jv_is_backwards1 = BoolProperty(name="Turn Backwards?", default=False, update=update_stairs)
# winding
tp.jv_winding_rot = EnumProperty(name="", items=(("1", "-90", ""), ("2", "-45", ""), ("3", "45", ""),
                                                        ("4", "90", "")), default="3", update=update_stairs)
tp.jv_step_begin_rot = IntProperty(name="Stair To Begin Rotation On", update=update_stairs, min=1, max=13,
                                         default=6)
# spiral
tp.jv_spiral_rot = FloatProperty(name="Total Rotation", unit="ROTATION", min=radians(-720), max=radians(720),
                                       default=radians(90), update=update_stairs)
tp.jv_pole_dia = FloatProperty(name="Pole Diameter", min=3.0 / METRIC_INCH, max=10.0 / METRIC_INCH,
                                            default=4.0 / METRIC_INCH, subtype="DISTANCE", update=update_stairs)
tp.jv_pole_res = IntProperty(name="Pole Resolution", min=8, max=64, default=16, update=update_stairs)
tp.jv_tread_res = IntProperty(name="Tread Resolution", min=0, max=8, default=0, update=update_stairs)
# stairs
tp.jv_im_scale2 = FloatProperty(name="Image Scale", max=10.0, min=0.1, default=1.0,
                                             description="Change Image Scaling")
tp.jv_col_image2 = StringProperty(name="", subtype="FILE_PATH", description="File Path For Color Image")
tp.jv_is_bump2 = BoolProperty(name="Normal Map?", default=False, description="Add Normal To Material?")
tp.jv_norm_image2 = StringProperty(name="", subtype="FILE_PATH",
                                                description="Filepath For Normal Map Image")
tp.jv_bump_amo2 = FloatProperty(name="Normal Stength", min=0.001, max=2.000, default=0.250,
                                             description="Normal Map Strength")
tp.jv_is_rotate2 = BoolProperty(name="Rotate Image?", default=False, description="Rotate Image 90 Degrees")
