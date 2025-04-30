import os

import orjson

from gltf_combiner.extensions.flatbuffer import deserialize_glb_json
from gltf_combiner.gltf.chunk import Chunk
from gltf_combiner.gltf.exceptions import AnimationNotFoundException
from gltf_combiner.gltf.gltf import GlTF
from gltf_combiner.streams import ByteReader, ByteWriter

JSON_CHUNK_TYPE = b"JSON"
FLATBUFFER_CHUNK_TYPE = b"FLA2"
BIN_CHUNK_TYPE = b"BIN\x00"

JSON_REPLACEMENT_LIST = ("textures", "images")
JSON_SKIP_LIST = ("buffers", "skins", "nodes", "scenes", "meshes")


def build_combined_gltf(
    geometry_filepath: os.PathLike | str, animation_filepath: os.PathLike | str, *, fix_texcoords: bool = False
) -> GlTF:
    geometry_gltf = GlTF().parse(geometry_filepath)
    animation_gltf = GlTF().parse(animation_filepath)

    return _build_combined_gltf(geometry_gltf, animation_gltf, fix_texcoords=fix_texcoords)


def rebuild_gltf(
    geometry_filepath: os.PathLike | str, *, fix_texcoords: bool = False
) -> GlTF:
    geometry_gltf = GlTF().parse(geometry_filepath)

    geometry_json_chunk = geometry_gltf.get_chunk_by_type(JSON_CHUNK_TYPE)
    geometry_flatbuffer_chunk = geometry_gltf.get_chunk_by_type(FLATBUFFER_CHUNK_TYPE)
    geometry_bin_chunk = geometry_gltf.get_chunk_by_type(BIN_CHUNK_TYPE)

    # Checking info chunks
    assert geometry_json_chunk is not None or geometry_flatbuffer_chunk is not None

    # Checking data chunks
    assert geometry_bin_chunk is not None

    geometry_json = (
        geometry_json_chunk.json()
        if geometry_json_chunk
        else deserialize_glb_json(geometry_flatbuffer_chunk.data)
    )

    _patch_accessor_component_types(geometry_json)
    if fix_texcoords:
        geometry_bin_chunk.data = _fix_texcoord(geometry_json, geometry_bin_chunk.data)

    new_json_chunk = Chunk(JSON_CHUNK_TYPE, orjson.dumps(geometry_json))

    return GlTF([new_json_chunk, geometry_bin_chunk])


def _build_combined_gltf(
    geometry_gltf: GlTF, animation_gltf: GlTF, *, fix_texcoords: bool
) -> GlTF:
    geometry_json_chunk = geometry_gltf.get_chunk_by_type(JSON_CHUNK_TYPE)
    geometry_flatbuffer_chunk = geometry_gltf.get_chunk_by_type(FLATBUFFER_CHUNK_TYPE)
    geometry_bin_chunk = geometry_gltf.get_chunk_by_type(BIN_CHUNK_TYPE)

    animation_json_chunk = animation_gltf.get_chunk_by_type(JSON_CHUNK_TYPE)
    animation_flatbuffer_chunk = animation_gltf.get_chunk_by_type(FLATBUFFER_CHUNK_TYPE)
    animation_bin_chunk = animation_gltf.get_chunk_by_type(BIN_CHUNK_TYPE)

    # Checking info chunks
    assert geometry_json_chunk is not None or geometry_flatbuffer_chunk is not None
    assert animation_json_chunk is not None or animation_flatbuffer_chunk is not None

    # Checking data chunks
    assert geometry_bin_chunk is not None
    assert animation_bin_chunk is not None

    geometry_json = (
        geometry_json_chunk.json()
        if geometry_json_chunk
        else deserialize_glb_json(geometry_flatbuffer_chunk.data)
    )
    animation_json = (
        animation_json_chunk.json()
        if animation_json_chunk
        else deserialize_glb_json(animation_flatbuffer_chunk.data)
    )

    if not ("animations" in animation_json):
        raise AnimationNotFoundException("animations node wasn't found")

    _update_json(geometry_json, animation_json)
    if fix_texcoords:
        geometry_bin_chunk.data = _fix_texcoord(geometry_json, geometry_bin_chunk.data)

    joined_dictionary = _join_dictionaries(geometry_json, animation_json)

    new_json_chunk = Chunk(JSON_CHUNK_TYPE, orjson.dumps(joined_dictionary))
    new_bin_chunk = Chunk(
        BIN_CHUNK_TYPE, geometry_bin_chunk.data + animation_bin_chunk.data
    )

    return GlTF([new_json_chunk, new_bin_chunk])


def _fix_texcoord(geometry_json: dict, data: bytes) -> bytes:
    buffer_bytes: list[bytearray] = []
    for buffer in geometry_json["buffers"]:
        if len(buffer) > 1:
            raise Exception("unsupported (not tested yet)")

        buffer_offset = buffer.get("byteOffset", 0)
        buffer_length = buffer["byteLength"]

        buffer_bytes.append(
            bytearray(data[buffer_offset : buffer_offset + buffer_length])
        )

    for mesh in geometry_json["meshes"]:
        primitive: dict[str, dict[str, int]]
        for primitive in mesh["primitives"]:
            for attribute_name, accessor_id in primitive["attributes"].items():
                if attribute_name.startswith("TEXCOORD_"):
                    _fix_texcoord_accessor(geometry_json, buffer_bytes, accessor_id)

    updated_buffer = bytearray()
    for i, buffer in enumerate(geometry_json["buffers"]):
        buffer_offset = buffer.get("byteOffset", 0)
        buffer_length = buffer["byteLength"]

        updated_buffer[buffer_offset : buffer_offset + buffer_length] = buffer_bytes[i]

    return updated_buffer


def _fix_texcoord_accessor(
    geometry_json: dict[str, dict], buffer_bytes: list[bytes], accessor_id: int
) -> None:
    def fix_value_u_int16(read_buffer: ByteReader, write_buffer: ByteWriter) -> None:
        write_buffer.write_u_int16(round(read_buffer.read_u_int16() * 65535 / 4096))

    def fix_value_int16(read_buffer: ByteReader, write_buffer: ByteWriter) -> None:
        write_buffer.write_int16(round(read_buffer.read_int16() * 32678 / 4096))

    fix_functions = {
        5122: fix_value_int16,
        5123: fix_value_u_int16,
    }

    accessor: dict = geometry_json["accessors"][accessor_id]
    accessor["normalized"] = True

    buffer_view_index = accessor["bufferView"]
    buffer_view = geometry_json["bufferViews"][buffer_view_index]
    buffer_view_offset = buffer_view["byteOffset"]
    buffer_view_length = buffer_view["byteLength"]

    accessor_offset = accessor.get("byteOffset", 0)

    buffer_index = buffer_view["buffer"]
    offset = buffer_view_offset + accessor_offset
    buffer_view_bytearray = buffer_bytes[buffer_index][
        offset : offset + buffer_view_length
    ]

    buffer_reader = ByteReader(buffer_view_bytearray, "little")

    component_type = accessor["componentType"]
    fix_value = fix_functions.get(component_type, None)
    if fix_value is None:
        raise Exception(f"Accessor component type is not supported: {component_type}")

    fixed_buffer = ByteWriter("little")
    for i in range(accessor["count"]):
        fix_value(buffer_reader, fixed_buffer)
        fix_value(buffer_reader, fixed_buffer)

    buffer_bytes[buffer_index][
        offset : offset + len(fixed_buffer.buffer)
    ] = fixed_buffer.buffer


def _patch_accessor_component_types(data: dict):
    for accessor in data["accessors"]:
        # Remove Supercell's mark of accessor type
        accessor["componentType"] &= 0x0000FFFF


def _update_json(geometry_json: dict, animation_json: dict) -> None:
    geometry_buffer_length = geometry_json["buffers"][0]["byteLength"]
    geometry_buffer_view_count = len(geometry_json["bufferViews"])
    geometry_buffer_accessor_count = len(geometry_json["accessors"])
    nodes_mapping = _get_nodes_mapping(geometry_json, animation_json)

    _patch_accessor_component_types(geometry_json)
    _patch_accessor_component_types(animation_json)
    _update_buffer(geometry_json, animation_json["buffers"][0]["byteLength"])
    _update_buffer_views(animation_json, geometry_buffer_length)
    _update_accessors(animation_json, geometry_buffer_view_count)
    _update_animations(animation_json, geometry_buffer_accessor_count, nodes_mapping)


def _update_buffer(geometry_json: dict, animation_buffer_length: int) -> None:
    _add_to_dict_value(
        geometry_json["buffers"][0],
        "byteLength",
        animation_buffer_length,
    )


def _update_buffer_views(animation_json: dict, geometry_buffer_length: int) -> None:
    for buffer_view in animation_json["bufferViews"]:
        _add_to_dict_value(buffer_view, "byteOffset", geometry_buffer_length)


def _update_accessors(animation_json: dict, geometry_buffer_view_count: int) -> None:
    for accessor in animation_json["accessors"]:
        _add_to_dict_value(accessor, "bufferView", geometry_buffer_view_count)


def _get_nodes_mapping(
    geometry_json: dict,
    animation_json: dict,
) -> dict[int, int]:
    nodes_mapping: dict[int, int] = {}

    geometry_nodes: list[dict[str, object]] = list(geometry_json["nodes"])
    animation_nodes: list[dict[str, object]] = animation_json["nodes"]
    for animation_node_index, animation_node in enumerate(animation_nodes):
        for geometry_node_index, geometry_node in enumerate(geometry_nodes):
            if (
                geometry_node["name"] == animation_node["name"]
                and "mesh" not in geometry_node
            ):
                nodes_mapping[animation_node_index] = geometry_node_index
                break

    return nodes_mapping


def _update_animations(
    animation_json: dict,
    geometry_buffer_accessor_count: int,
    nodes_mapping: dict[int, int],
) -> None:
    for animation in animation_json["animations"]:
        for sampler in animation["samplers"]:
            _add_to_dict_value(sampler, "input", geometry_buffer_accessor_count)
            _add_to_dict_value(sampler, "output", geometry_buffer_accessor_count)

        channels: list = animation["channels"]
        filtered_channels = list(
            filter(
                lambda channel1: channel1["target"]["node"] in nodes_mapping, channels
            )
        )

        if (deleted_channel_count := len(channels) - len(filtered_channels)) > 0:
            animation["channels"] = filtered_channels
            print(
                f"Some animation channels ({deleted_channel_count}) are deleted... "
                f"{len(filtered_channels)} out of {len(channels)} left."
            )
            # TODO: log about number of deleted channels into the console
            # TODO: check if all channels are deleted and throw an exception

        for channel in filtered_channels:
            channel["target"]["node"] = nodes_mapping[channel["target"]["node"]]


def _join_dictionaries(geometry_json: dict, animation_json: dict) -> dict:
    joined_dict = dict(**geometry_json)

    for key, value in animation_json.items():
        if isinstance(value, list):
            if joined_dict.get(key) is None or key in JSON_REPLACEMENT_LIST:
                joined_dict[key] = value
            elif joined_dict[key] == value or key in JSON_SKIP_LIST:
                continue

            joined_dict[key].extend(value)

    return joined_dict


def _add_to_dict_value(dictionary: dict, key: str, value_to_add: int) -> None:
    dictionary[key] = dictionary.get(key, 0) + value_to_add
