from . jv_flooring import JVFlooring
from . jv_siding import JVSiding


registered_types = {
    "flooring": JVFlooring,
    "siding": JVSiding
}


def get_object_type_handler(object_type: str):
    return registered_types.get(object_type, None)
