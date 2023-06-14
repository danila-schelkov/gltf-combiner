import orjson

from gltf_combiner.gltf.chunk import Chunk
from gltf_combiner.gltf.gltf import GlTF

JSON_REPLACEMENT_LIST = ("textures", "images")
JSON_SKIP_LIST = ("buffers", "skins", "nodes", "scenes")


def main() -> None:
    geometry_gltf = GlTF().parse("../test/resources/maisie_geo.glb")
    animation_gltf = GlTF().parse("../test/resources/maisie_win.glb")

    geometry_json: dict = geometry_gltf.get_chunk_by_type(b"JSON").json()
    animation_json: dict = animation_gltf.get_chunk_by_type(b"JSON").json()

    geometry_buffers: list[dict] = geometry_json["buffers"]

    geometry_buffer_views: list[dict] = geometry_json["bufferViews"]
    geometry_buffer_view_count = len(geometry_buffer_views)

    geometry_buffer_accessors: list[dict] = geometry_json["accessors"]
    geometry_buffer_accessor_count = len(geometry_buffer_accessors)

    geometry_buffer_nodes: list[dict] = geometry_json["nodes"]
    geometry_buffer_node_count = len(geometry_buffer_nodes)

    geometry_buffer_length = geometry_buffers[0]["byteLength"]
    add_to_dict_value(geometry_buffers[0], "byteLength", animation_json["buffers"][0]["byteLength"])

    for buffer_view in animation_json["bufferViews"]:
        add_to_dict_value(buffer_view, "byteOffset", geometry_buffer_length)

    for accessor in animation_json["accessors"]:
        add_to_dict_value(accessor, "bufferView", geometry_buffer_view_count)

    geometry_json["skins"] = geometry_json["skins"]
    for skin in animation_json["skins"]:
        skin["joints"] = [joint + geometry_buffer_node_count
                          for joint in skin["joints"]]
        add_to_dict_value(skin, "inverseBindMatrices", geometry_buffer_accessor_count)

    for animation in animation_json["animations"]:
        for sampler in animation["samplers"]:
            add_to_dict_value(sampler, "input", geometry_buffer_accessor_count)
            add_to_dict_value(sampler, "output", geometry_buffer_accessor_count)
        for channel in animation["channels"]:
            add_to_dict_value(channel["target"], "node", 7)

    for node in animation_json["nodes"]:
        if "children" not in node:
            continue

        node["children"] = [child_node + geometry_buffer_node_count
                            for child_node in node["children"]]

    for scene in animation_json["scenes"]:
        scene["nodes"] = [node + geometry_buffer_node_count
                          for node in scene["nodes"]]

    for key, value in animation_json.items():
        if isinstance(value, list):
            if geometry_json.get(key) is None or key in JSON_REPLACEMENT_LIST:
                geometry_json[key] = value
            elif geometry_json[key] == value or key in JSON_SKIP_LIST:
                continue
            else:
                geometry_json[key].extend(value)
            # print(key, geometry_json[key])
            continue

    new_bin_data = (
            geometry_gltf.get_chunk_by_type(b"BIN\x00").data
            + animation_gltf.get_chunk_by_type(b"BIN\x00").data
    )

    new_json_chunk = Chunk(b"JSON", orjson.dumps(geometry_json))
    new_bin_chunk = Chunk(b"BIN\x00", new_bin_data)

    filepath = "../test/resources/new.glb"

    gltf = GlTF([new_json_chunk, new_bin_chunk])
    gltf.write(filepath)

    print(f"Done! Saved to the \"{filepath}\".")


def add_to_dict_value(dictionary: dict, key: str, value_to_add: int) -> None:
    dictionary[key] = dictionary[key] + value_to_add


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit(0)
