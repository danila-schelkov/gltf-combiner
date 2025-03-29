# ! ---------------- Serializing ----------------
from enum import IntEnum

from flatbuffers import flexbuffers, Builder
from flatbuffers.compat import import_numpy

from .generated import glTF_generated as flat

np = import_numpy()

from .common import pascal_case
from .schema import gltf_schema


def _serialize_gather(builder: Builder, class_name: str, gather: dict) -> any:
    """
    A place where dark magic happens.
    Serializes a dictionary `gather` into a flatbuffer using the
    provided `Builder` and class.

    :param builder: File builder
    :param class_name: Class name
    :param gather: dictionary containing gathered data to be serialized. The
    keys of the dictionary represent the fields or attributes of the object, and the values represent
    the corresponding values of those fields
    :return: the result of calling the `EndObject` function on the `builder` object.
    """

    start_function = getattr(flat, f"{class_name}Start")
    end_function = getattr(flat, f"{class_name}End")

    start_function(builder)
    for key, value in reversed(gather.items()):
        add_function = getattr(flat, f"{class_name}Add{key}")
        add_function(builder, value)

    return end_function(builder)


def _serialize_array(
    builder: Builder, data: list, schema: any, class_name: str, key: str
) -> int or list:
    if schema == int:
        array = np.array(data, dtype=np.int32)
        return builder.CreateNumpyVector(array)

    elif schema == float:
        array = np.array(data, dtype=np.float32)
        return builder.CreateNumpyVector(array)

    elif isinstance(schema, dict) or schema == str:
        objects = []

        for element in data:
            if element is None:
                continue

            if schema == str:
                objects.append(builder.CreateString(element))
            else:
                objects.append(_serialize_flatbuffer(builder, element, schema))

        object_count = len(objects)
        if object_count == 0:
            return 0
        vector_start = getattr(flat, f"{class_name}Start{key}Vector")
        vector_start(builder, object_count)

        for element in reversed(objects):
            builder.PrependUOffsetTRelative(element)

        return builder.EndVector()


def _serialize_flatbuffer(builder: Builder, data: dict, schema: dict) -> any:
    gather = {}

    class_name = schema.get("_type").__name__
    for key, value in schema.items():
        if key.startswith("_"):
            continue

        key_getter = pascal_case(key)
        key_data = data.get(key)
        if key_data is None:
            continue

        value_type = value
        default_value = None
        if isinstance(value, tuple):
            value_type, default_value = value

        if key_data == default_value:
            continue

        # Simple Types
        if value_type == int or value_type == float or value_type == bool:
            gather[key_getter] = key_data

        # Strings
        if value_type == str:
            gather[key_getter] = builder.CreateString(key_data)

        # FlexBuffers
        elif value_type == bytes:
            gather[key_getter] = builder.CreateByteVector(flexbuffers.Dumps(key_data))

        # Array Of Objects
        elif isinstance(value_type, list):
            gather[key_getter] = _serialize_array(
                builder, key_data, schema[key][0], class_name, key_getter
            )

        # Structs
        elif isinstance(value_type, dict):
            gather[key_getter] = _serialize_flatbuffer(builder, key_data, schema[key])

        # String-Enum
        elif issubclass(value_type, IntEnum):
            enum_data = getattr(value_type, key_data)
            if enum_data == default_value:
                continue
            gather[key_getter] = enum_data.value

    return _serialize_gather(builder, class_name, gather)


def serialize_glb_json(data: dict) -> bytes:
    flatbuffer = Builder()

    root = _serialize_flatbuffer(flatbuffer, data, gltf_schema)

    flatbuffer.Finish(root)
    return bytes(flatbuffer.Output())
