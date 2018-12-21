from . jv_flooring import JVFlooring


registered_types = {
    "flooring": JVFlooring
}


def get_object_type_handler(object_type: str):
    return registered_types.get(object_type, None)
