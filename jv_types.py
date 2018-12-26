from . jv_flooring import JVFlooring
from . jv_siding import JVSiding
from . jv_roofing import JVRoofing


registered_types = {
    "flooring": JVFlooring,
    "siding": JVSiding,
    "roofing": JVRoofing
}


def get_object_type_handler(object_type: str):
    return registered_types.get(object_type, None)
