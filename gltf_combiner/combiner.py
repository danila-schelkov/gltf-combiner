import os

import orjson

from gltf_combiner.gltf.chunk import Chunk
from gltf_combiner.gltf.exceptions import AnimationNotFoundException
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

    if not ("animations" in animation_json):
        raise AnimationNotFoundException("animations node wasn't found")

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
    nodes_mapping = _get_nodes_mapping(geometry_json, animation_json)

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
                f"Some animation channels are deleted... "
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
