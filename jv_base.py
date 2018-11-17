from bpy.types import PropertyGroup
from bpy.props import FloatProperty

MI = 39.3701
MF = 3.28084
IN = 1 / MI
HIN = 0.5 / MI


class JVBase(PropertyGroup):
    def __init__(self, obj, is_converted=False):
        self.object = obj
        self.is_converted = is_converted

    def _verts(self) -> list:
        pass

    def _faces(self) -> list:
        pass

    def update(self):
        pass

    def draw(self, layout):
        pass

    @staticmethod
    def build_general_property(prop_name):
        props = {
            "over_width": (FloatProperty, {
                "name": "Overall Width",
                "default": 20 / MF,
                "description": "Overall Width",
                "subtype": "DISTANCE"
            })
        }

        if prop_name in props:
            return props[prop_name][0](**props[prop_name][1])
        else:
            return None

# bpy.utils.register_class(JVBase)
