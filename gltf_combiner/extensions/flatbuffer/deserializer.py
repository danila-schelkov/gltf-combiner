from collections import OrderedDict
from enum import IntEnum

from flatbuffers import flexbuffers
from flatbuffers.compat import import_numpy

from ..flatbuffer.common import pascal_case
from ..flatbuffer.generated.glTF_generated import Root
from ..flatbuffer.preprocessor import Preprocessor
from ..flatbuffer.schema import gltf_schema

np = import_numpy()


def _deserialize_string(data: bytes | None) -> str | None:
    if data is None:
        return None

    return data.decode("utf8")


def _deserialize_flexbuffer(data) -> any:
    if isinstance(data, int) and data == 0:
        return None

    data_array = bytearray(data)
    try:
        return flexbuffers.Loads(data_array)
    except:
        pass


def _deserialize_array(buffer: any, key: str, schema: any) -> list | None:
    # List of numbers
    if schema == int or schema == float:
        number_array = getattr(buffer, f"{key}AsNumpy")()
        if isinstance(number_array, int) and number_array == 0:
            return None
        return number_array.tolist()

    # Structs | strings
    elif isinstance(schema, dict) or schema == str:
        result = []
        object_number = getattr(buffer, f"{key}Length")()
        for i in range(object_number):
            object_buffer = getattr(buffer, key)(i)
            if schema == str:
                result.append(bytes(object_buffer).decode("utf8"))
            else:
                result.append(_deserialize_flatbuffer(object_buffer, schema))

        return result


def _deserialize_flatbuffer(buffer: any, schema: dict) -> dict:
    result = OrderedDict()

    for key, value in schema.items():
        getter_key = pascal_case(key)
        value_type = value
        default_value = None
        value_data = None

        if isinstance(value_type, tuple):
            value_type, default_value = value

        # Numbers & Booleans | Simple Types
        if value_type == int or value_type == bool or value_type == float:
            value_data = getattr(buffer, getter_key)()

        # Strings
        elif value_type == str:
            value_data = _deserialize_string(getattr(buffer, getter_key)())

        # FlexBuffers
        elif value_type == bytes:
            value_data = _deserialize_flexbuffer(
                getattr(buffer, f"{getter_key}AsNumpy")()
            )

        # Array Of Objects
        elif isinstance(value_type, list):
            value_data = _deserialize_array(buffer, getter_key, value_type[0])

        # Structs
        elif isinstance(value_type, dict):
            struct_buffer = getattr(buffer, getter_key)()
            if struct_buffer is None:
                continue

            value_data = _deserialize_flatbuffer(struct_buffer, schema[key])

        # String-Enum
        elif issubclass(value_type, IntEnum):
            enum_value = getattr(buffer, getter_key)()
            if enum_value == default_value:
                continue
            value_data = value_type(enum_value).name

        if default_value != value_data:
            result[key] = value_data if value_data is not None else default_value

    return result


def deserialize_buffer_to_dict(data: bytes) -> dict:
    """
    The function takes bytes of glTF FLA2 chunk data and returns a dictionary
    containing the deserialized JSON data.

    :param data: A bytes that represents glTF FLA2 chunk data
    :return: JSON data in python dict that can be used for serialization to usual json or using in python
    """
    flatbuffer = Root.GetRootAs(bytearray(data))

    output = _deserialize_flatbuffer(flatbuffer, gltf_schema)

    return Preprocessor.preprocess_data(output)
