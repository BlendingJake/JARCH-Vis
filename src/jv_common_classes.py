from enum import StrEnum

from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, Object
from bpy.utils import register_classes_factory


class BisectingPlane(PropertyGroup):
    normal: FloatVectorProperty(name="Normal", size=3, unit="LENGTH")

    # LOCAL
    center: FloatVectorProperty(name="Center", size=3, unit="LENGTH")


class FaceGroup(PropertyGroup):
    """A group of faces that belong together and lie in the same plane
    which will be converted into a single instance of architecture.
    """

    face_indices: StringProperty(name="Face Indices (CSV)", default="")

    is_convex: BoolProperty(
        name="Convex?",
        description="Are the faces convex? Aka, are all interior angles <= 180 degrees and there are no cutouts?",
    )

    boolean_object: PointerProperty(name="Bolean Object", type=Object)

    # the rotation of the face group from the X-Y plane
    rotation: FloatVectorProperty(subtype="EULER", size=3)

    # LOCAL coordinate of bottom-left corner
    location: FloatVectorProperty(subtype="TRANSLATION", size=3)

    dimensions: FloatVectorProperty(unit="LENGTH", size=2)

    bisecting_planes: CollectionProperty(name="Bisecting Planes", type=BisectingPlane)


class RoofingPattern(StrEnum):
    """The unique names for all of the types of roofing which are
    supported. These are the keys given to the EnumProperty which
    can then be used for comparison checks later.
    """

    Shakes = "shakes"
    Shingles3Tab = "shingles_3_tab"
    ShinglesArchitectural = "shingles_architectural"
    Terracotta = "terracotta"
    TinAngular = "tin_angular"
    TinRegular = "tin_regular"
    TinStandingSeam = "tin_standing_seam"


class Units:
    """Pre-defined Imperial units that have been translated to meters, the
    unit Blender uses under the hood.
    """

    FOOT: float = 1 / 3.248
    INCH: float = FOOT / 12
    TQ_INCH: float = INCH * 0.75
    """3/4 inch"""
    H_INCH: float = INCH / 2
    """1/2 inch"""
    Q_INCH: float = H_INCH / 2
    """1/4 inch"""
    ETH_INCH: float = INCH / 8
    """1/8 inch"""
    STH_INCH: float = INCH / 16
    """1/16 inch"""


register, unregister = register_classes_factory([BisectingPlane, FaceGroup])
