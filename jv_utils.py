from bpy.props import FloatProperty

MI = 39.3701
MF = 3.28084
IN = 1 / MI
HIN = 0.5 / MI


def build_general_property(prop_name):
    """
    Build default properties that are used by several subclasses. props: prop_name -> (PropertyClass, {attributes})
    :param prop_name: The name of the property to build
    :return: None if the property name cannot be found, otherwise, create a new property and return it
    """

    props = {
        "width": (FloatProperty, {
            "name": "Overall Width",
            "default": 20 / MF,
            "description": "Overall Width",
            "subtype": "DISTANCE"
        }),

        "length": (FloatProperty, {
            "name": "Overall Length",
            "default": 8 / MF,
            "description": "Overall Length",
            "subtype": "DISTANCE"
        })
    }

    if prop_name in props:
        return props[prop_name][0](**props[prop_name][1])
    else:
        return None
