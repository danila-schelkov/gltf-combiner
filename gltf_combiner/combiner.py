import os

import orjson

from gltf_combiner.gltf.chunk import Chunk
from gltf_combiner.gltf.gltf import GlTF

JSON_REPLACEMENT_LIST = ("textures", "images")
JSON_SKIP_LIST = ("buffers", "skins", "nodes", "scenes")


def build_combined_gltf(
    geometry_filepath: os.PathLike | str, animation_filepath: os.PathLike | str
) -> GlTF:
    geometry_gltf = GlTF().parse(geometry_filepath)
    animation_gltf = GlTF().parse(animation_filepath)

    return _build_combined_gltf(geometry_gltf, animation_gltf)


def _build_combined_gltf(geometry_gltf: GlTF, animation_gltf: GlTF) -> GlTF:
    geometry_json_chunk = geometry_gltf.get_chunk_by_type(b"JSON")
    animation_json_chunk = animation_gltf.get_chunk_by_type(b"JSON")
    geometry_bin_chunk = geometry_gltf.get_chunk_by_type(b"BIN\x00")
    animation_bin_chunk = animation_gltf.get_chunk_by_type(b"BIN\x00")
    assert geometry_json_chunk is not None
    assert geometry_bin_chunk is not None
    assert animation_json_chunk is not None
    assert animation_bin_chunk is not None

    geometry_json = geometry_json_chunk.json()
    animation_json = animation_json_chunk.json()

    _update_json(geometry_json, animation_json)

    joined_dictionary = _join_dictionaries(geometry_json, animation_json)

    new_json_chunk = Chunk(b"JSON", orjson.dumps(joined_dictionary))
    new_bin_chunk = Chunk(
        b"BIN\x00", geometry_bin_chunk.data + animation_bin_chunk.data
    )

    return GlTF([new_json_chunk, new_bin_chunk])


def _update_json(geometry_json: dict, animation_json: dict) -> None:
    geometry_buffer_length = geometry_json["buffers"][0]["byteLength"]
    geometry_buffer_view_count = len(geometry_json["bufferViews"])
    geometry_buffer_accessor_count = len(geometry_json["accessors"])
    geometry_geom_node_count = len(geometry_json["nodes"]) - len(
        animation_json["nodes"]
    )

    _update_buffer(geometry_json, animation_json["buffers"][0]["byteLength"])
    _update_buffer_views(animation_json, geometry_buffer_length)
    _update_accessors(animation_json, geometry_buffer_view_count)
    _update_animations(
        animation_json, geometry_buffer_accessor_count, geometry_geom_node_count
    )


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


def _update_animations(
    animation_json: dict,
    geometry_buffer_accessor_count: int,
    geometry_geom_node_count: int,
) -> None:
    for animation in animation_json["animations"]:
        for sampler in animation["samplers"]:
            _add_to_dict_value(sampler, "input", geometry_buffer_accessor_count)
            _add_to_dict_value(sampler, "output", geometry_buffer_accessor_count)
        for channel in animation["channels"]:
            # TODO: check how it works and if it fails, then just map nodes by names
            _add_to_dict_value(channel["target"], "node", geometry_geom_node_count)


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
    dictionary[key] = dictionary[key] + value_to_add
