import numpy as np
import orjson

from gltf_combiner.streams import ByteReader, ByteWriter

from ...gltf import BIN_CHUNK_TYPE, FLATBUFFER_CHUNK_TYPE, JSON_CHUNK_TYPE, Chunk, GlTF
from ..flatbuffer import deserialize_glb_json
from .gltf_constants import ComponentType, DataType
from .odin_attribute import OdinAttribute
from .odin_constants import OdinAttributeFormat, OdinAttributeType

## Exclusive Accessor Component Types
# 1 - Float Vector 3
# 2 - Float Vector 4
# 3 - Matrix4x4
# Idk what sense of modifying component type
# Maybe it more like GPU hint or smth like this


class BufferView:
    def __init__(self) -> None:
        self.stride: int | None = None
        self.offset: int | None = None
        self.data: bytes = b""

    def serialize(self):
        data = {
            "buffer": 0,
            "byteOffset": self.offset,
            "byteLength": len(self.data),
        }

        if self.stride is not None:
            data["byteStride"] = self.stride

        return data


class SupercellOdinGLTF:
    used_extensions = [
        # "KHR_mesh_quantization",
        # "KHR_texture_transform",
        "SC_shader"
    ]

    required_extensions = [
        # "KHR_mesh_quantization"
    ]

    def __init__(self, gltf: GlTF) -> None:
        self._buffers: list[BufferView] = []
        self._odin_buffer_index: int = -1
        self._mesh_descriptors: list[dict] = []

        json_chunk = gltf.get_chunk_by_type(JSON_CHUNK_TYPE)
        flatbuffer_chunk = gltf.get_chunk_by_type(FLATBUFFER_CHUNK_TYPE)

        # Checking info chunks
        assert json_chunk is not None or flatbuffer_chunk is not None

        self._data: dict = (
            json_chunk.json()
            if json_chunk
            else deserialize_glb_json(flatbuffer_chunk.data)
        )

        bin_chunk = gltf.get_chunk_by_type(BIN_CHUNK_TYPE)

        # Checking data chunks
        assert bin_chunk is not None

        self._produce_buffers(bin_chunk.data)

    def remove_odin(self) -> GlTF:
        self.process_meshes_raw()
        self.process_accessors()
        self.process_skins()
        self.process_nodes()

        extensions_required: list[str] = self._data.get("extensionsRequired", [])
        extensions_used: list[str] = self._data.get("extensionsUsed", [])

        has_odin = False
        if "SC_odin_format" in extensions_required:
            extensions_required.remove("SC_odin_format")
            has_odin = True

        if "SC_odin_format" in extensions_used:
            extensions_used.remove("SC_odin_format")
            has_odin = True

        if has_odin:
            self.initialize_odin()
            self.process_meshes()

        return self.save()

    def process_accessors(self) -> None:
        accessors: list[dict] = self._data.get("accessors", [])

        for accessor in accessors:
            component = accessor["componentType"]

            # Masking Supercell custom index to make it valid
            accessor["componentType"] = component & 0x0000FFFF

    def process_meshes_raw(self) -> None:
        meshes: list[dict] = self._data.get("meshes", [])

        for mesh in meshes:
            primitives: dict = mesh.get("primitives")
            if primitives is None:
                continue

            empty_primitives: list[int] = []

            for i, primitive in enumerate(primitives):
                # Empty primitives in animations bugfix
                if "attributes" not in primitive and "extensions" not in primitive:
                    empty_primitives.append(i)

                # Targets type bugfix
                targets = primitive.get("targets")
                if isinstance(targets, dict):
                    primitive.pop("targets")

            if new_primitives := [
                primitive
                for i, primitive in enumerate(primitives)
                if i not in empty_primitives
            ]:
                mesh["primitives"] = new_primitives
            else:
                mesh.pop("primitives")

    def process_nodes(self) -> None:
        nodes: list[dict] = self._data.get("nodes", [])

        children: dict[int, list[int]] = {}

        def add_child(index: int, parent_index: int):
            if parent_index not in children:
                children[parent_index] = []
            children[parent_index].append(index)

        for i, node in enumerate(nodes):
            extensions: dict = node.get("extensions", {})
            if "SC_odin_format" not in extensions:
                continue

            odin: dict[str, int] = extensions.pop("SC_odin_format")
            parent = odin.get("parent")
            add_child(i, parent)

        for idx, children in children.items():
            nodes[idx]["children"] = children

    def process_skins(self) -> None:
        skins: list[dict] = self._data.get("skins", [])

        for skin in skins:
            extensions: dict = skin.get("extensions", {})
            if "SC_odin_format" not in extensions:
                continue

            extensions.pop("SC_odin_format")

    def process_meshes(self) -> None:
        meshes: list[dict] = self._data.get("meshes", [])

        for mesh in meshes:
            extensions: dict = mesh.get("extensions", {})
            if "SC_odin_format" in extensions:
                extensions.pop("SC_odin_format")

            primitives = mesh.get("primitives")
            if primitives is None:
                continue

            for primitive in primitives:
                self.process_mesh_primitive(primitive)

    def process_mesh_primitive(self, primitive: dict) -> None:
        extensions: dict = primitive.get("extensions", {})
        if "SC_odin_format" not in extensions:
            return

        odin = extensions.pop("SC_odin_format")
        indices = primitive.get("indices")
        count = self.calculate_odin_position_count(self._data["accessors"][indices])

        mesh_descriptor = (
            odin
            if "vertexDescriptors" in odin
            else self._mesh_descriptors[odin["meshDataInfoIndex"]]
        )
        vertex_descriptors: list[dict] = mesh_descriptor["vertexDescriptors"]

        attributes = {}
        for descriptor in vertex_descriptors:
            self.process_odin_primitive_descriptor(descriptor, attributes, count)

        primitive["attributes"] = attributes

    def process_odin_primitive_descriptor(
        self, descriptor: dict, attributes: dict, positions_count: int
    ):
        attribute_descriptor: list[OdinAttribute] = []
        attribute_buffers: list[np.array] = []
        attribute_accessors: list[np.array] = []

        offset = descriptor["offset"]
        stride = descriptor["stride"]

        for i, attribute in enumerate(descriptor["attributes"]):
            attribute_type_index = attribute["index"]
            attribute_format_index = attribute["format"]
            if attribute_type_index not in list(OdinAttributeType):
                print(f'Unknown attribute name "{attribute.get("name")}". Skip...')
                continue

            if attribute_format_index not in list(OdinAttributeFormat):
                print(
                    f'Unknown format "{attribute_format_index}" in attribute "{attribute.get("name")}". Skip...'
                )
                continue

            attribute_type = OdinAttributeType(attribute_type_index)
            attribute_format = OdinAttributeFormat(attribute_format_index)
            is_integer = attribute["interpretAsInteger"]
            attribute = OdinAttribute(
                attribute_type, attribute_format, attribute["offset"]
            )

            attribute_buffers.append(
                np.zeros(
                    (positions_count, attribute.elements_count),
                    dtype=attribute.data_type,
                )
            )
            attribute_descriptor.append(attribute)
            attribute_accessors.append(
                {
                    "bufferView": len(self._buffers) + i,
                    "componentType": OdinAttributeFormat.to_accessor_component(
                        attribute_format
                    ),
                    "normalized": not is_integer,
                    "count": int(positions_count),
                    "type": OdinAttributeFormat.to_accessor_type(attribute_format),
                }
            )

        mesh_buffer = self._buffers[self._odin_buffer_index].data
        for tris_idx in range(positions_count):
            for attr_idx, attribute in enumerate(attribute_descriptor):
                value_offset = offset + (stride * tris_idx) + attribute.offset
                buffer = attribute_buffers[attr_idx]
                buffer[tris_idx] = attribute.read(mesh_buffer, value_offset)

        for i, attribute in enumerate(attribute_descriptor):
            attribute_name = OdinAttributeType.to_attribute_name(attribute.type)
            attributes[attribute_name] = len(self._data["accessors"]) + i

            buffer_view = BufferView()
            buffer_view.data = attribute_buffers[i].tobytes()
            self._buffers.append(buffer_view)

        self._data["accessors"].extend(attribute_accessors)

    def process_animation(self, animation: dict) -> None:
        animations = self._data.get("animations", [])

        frame_rate = animation["frameRate"]
        frame_spf = 1.0 / frame_rate
        keyframes_count = animation["keyframeCount"]
        used_nodes = animation["nodes"]
        odin_animation_accessor = animation["accessor"]

        animation_transform_array = self.decode_accessor_obj(
            self._data["accessors"][odin_animation_accessor]
        )
        # Position + Quaternion Rotation + Scale
        frame_transform_length = 3 + 4 + 3
        animation_transform_array = np.reshape(
            animation_transform_array,
            (len(used_nodes), keyframes_count, frame_transform_length),
        )

        # Animation input
        animation_input_index = len(self._data["accessors"])
        animation_input_buffer = ByteWriter()
        for i in range(keyframes_count):
            animation_input_buffer.write_float(frame_spf * i)
        self._data["accessors"].append(
            {
                "bufferView": len(self._data["bufferViews"]),
                "componentType": 5126,
                "count": keyframes_count,
                "type": "SCALAR",
            }
        )
        buffer_view = BufferView()
        buffer_view.data = bytes(animation_input_buffer.buffer)
        self._buffers.append(buffer_view)

        # Animation Transform
        animation_buffers_indices: list[tuple[int, int, int]] = []
        animation_transform_buffers: list[tuple[ByteWriter, ByteWriter, ByteWriter]] = [
            (ByteWriter(), ByteWriter(), ByteWriter()) for _ in used_nodes
        ]
        for node_index in range(len(used_nodes)):
            for frame_index in range(keyframes_count):
                # print(node_index)
                translation, rotation, scale = animation_transform_buffers[node_index]
                t, r, s = np.array_split(
                    animation_transform_array[node_index][frame_index], [3, 7]
                )

                for value in t:
                    translation.write_float(value)

                for value in r:
                    rotation.write_float(value)

                for value in s:
                    scale.write_float(value)

        for buffer in animation_transform_buffers:
            translation, rotation, scale = buffer
            base_accessor_index = len(self._data["accessors"])
            base_bufferView_index = len(self._buffers)

            # Translation
            self._data["accessors"].append(
                {
                    "bufferView": base_bufferView_index,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC3",
                }
            )
            translation_buffer_view = BufferView()
            translation_buffer_view.data = bytes(translation.buffer)
            self._buffers.append(translation_buffer_view)

            # Rotation
            self._data["accessors"].append(
                {
                    "bufferView": base_bufferView_index + 1,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC4",
                }
            )
            rotation_buffer_view = BufferView()
            rotation_buffer_view.data = bytes(rotation.buffer)
            self._buffers.append(rotation_buffer_view)

            # Scale
            self._data["accessors"].append(
                {
                    "bufferView": base_bufferView_index + 2,
                    "componentType": 5126,
                    "count": keyframes_count,
                    "type": "VEC3",
                }
            )
            scale_buffer_view = BufferView()
            scale_buffer_view.data = bytes(scale.buffer)
            self._buffers.append(scale_buffer_view)

            animation_buffers_indices.append(
                (base_accessor_index, base_accessor_index + 1, base_accessor_index + 2)
            )

        # Animation channels
        animation_channels: list[dict] = []
        animation_samplers: list[dict] = []
        for node_number, node_index in enumerate(used_nodes):
            translation, rotation, scale = animation_buffers_indices[node_number]

            # Translation
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {"node": node_index, "path": "translation"},
                }
            )
            animation_samplers.append(
                {"input": animation_input_index, "output": translation}
            )

            # Rotation
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {"node": node_index, "path": "rotation"},
                }
            )
            animation_samplers.append(
                {"input": animation_input_index, "output": rotation}
            )

            # Scale
            animation_channels.append(
                {
                    "sampler": len(animation_samplers),
                    "target": {"node": node_index, "path": "scale"},
                }
            )
            animation_samplers.append({"input": animation_input_index, "output": scale})

        animations.append(
            {
                "name": "clip",
                "channels": animation_channels,
                "samplers": animation_samplers,
            }
        )

        self._data["animations"] = animations

        self.process_animation_skin(used_nodes)

    def process_animation_skin(self, nodes: list[int]) -> None:
        skins: list[dict] = self._data.get("skins", [])

        for skin in skins:
            joints: list[int] = skin["joints"]
            if all(joints):  # FIXME
                return

        new_skin_joints: list[int] = []

        def add_skin_joint(idx: int):
            node = self._data["nodes"][idx]
            children = node.get("children", [])
            for children in children:
                add_skin_joint(children)
            if idx not in new_skin_joints:
                new_skin_joints.append(idx)

        for node in nodes:
            add_skin_joint(node)

        skins.append({"joints": new_skin_joints})
        self._data["skins"] = skins

    def calculate_odin_position_count(self, accessor: dict) -> int:
        array = self.decode_accessor_obj(accessor)
        max_index = np.max(array)
        return max_index + 1

    def initialize_odin(self) -> None:
        extensions: dict = self._data.get("extensions")
        odin = extensions.pop("SC_odin_format")
        self._odin_buffer_index = odin["bufferView"]
        self._mesh_descriptors = odin.get("meshDataInfos", [])

        if "materials" in odin:
            self._data["materials"] = odin["materials"]

        if "animation" in odin:
            self.process_animation(odin["animation"])

        if "extensionsUsed" not in self._data:
            self._data["extensionsUsed"] = []
        self._data["extensionsUsed"].extend(SupercellOdinGLTF.used_extensions)

        if "extensionsRequired" not in self._data:
            self._data["extensionsRequired"] = []
        self._data["extensionsRequired"].extend(SupercellOdinGLTF.required_extensions)

    def _serialize_buffers(self) -> bytes:
        stream = ByteWriter()

        buffers: list[dict] = []
        buffer_view: list[dict] = []

        for buffer in self._buffers:
            buffer.offset = stream.position
            buffer_view.append(buffer.serialize())

            stream.write(buffer.data)
            stream.write(b"\0" * ((len(buffer.data) + 15) & ~15))  # padding

        buffers.append({"byteLength": len(stream.buffer)})

        self._data["buffers"] = buffers
        self._data["bufferViews"] = buffer_view

        return bytes(stream.buffer)

    def _produce_buffers(self, data: bytes) -> None:
        if "buffers" not in self._data:
            return

        if "bufferViews" not in self._data:
            return

        buffers: list[dict] = self._data["buffers"]
        buffer_views: list[dict] = self._data["bufferViews"]
        assert len(buffers) == 1

        stream = ByteReader(data)

        for bufferView in buffer_views:
            buffer_index = bufferView.get("buffer")
            assert buffer_index == 0

            offset = bufferView.get("byteOffset", 0)
            length = bufferView.get("byteLength")

            stream.seek(offset)
            data = stream.read(length)

            buffer = BufferView()
            buffer.stride = bufferView.get("byteStride", None)
            buffer.data = data
            self._buffers.append(buffer)

    def save(self) -> GlTF:
        return GlTF(
            Chunk(JSON_CHUNK_TYPE, orjson.dumps(self._data)),
            Chunk(BIN_CHUNK_TYPE, self._serialize_buffers()),
        )

    # https://github.com/KhronosGroup/glTF-Blender-IO/blob/da2172c284cd0576e3a63234ea893f9b4edcacca/addons/io_scene_gltf2/io/imp/gltf2_io_binary.py#L123
    def decode_accessor_obj(self, accessor: dict) -> np.array:
        # MAT2/3 have special alignment requirements that aren't handled. But it
        # doesn't matter because nothing uses them.
        assert accessor.get("type") not in ["MAT2", "MAT3"]

        dtype = ComponentType.to_numpy_dtype(accessor.get("componentType"))
        component_nb = DataType.num_elements(accessor.get("type"))

        buffer_view_index = accessor.get("bufferView")
        if buffer_view_index is not None:
            buffer_view = self._data["bufferViews"][buffer_view_index]
            buffer_data = self._buffers[buffer_view_index].data

            accessor_offset = accessor.get("byteOffset") or 0

            bytes_per_elem = dtype(1).nbytes
            default_stride = bytes_per_elem * component_nb
            stride = buffer_view.get("byteStride") or default_stride

            if stride == default_stride:
                array = np.frombuffer(
                    buffer_data,
                    dtype=np.dtype(dtype).newbyteorder("<"),
                    count=accessor.get("count") * component_nb,
                    offset=accessor_offset,
                )
                array = array.reshape(accessor.get("count"), component_nb)
            else:
                # The data looks like
                #   XXXppXXXppXXXppXXX
                # where X are the components and p are padding.
                # One XXXpp group is one stride's worth of data.
                assert stride % bytes_per_elem == 0
                elems_per_stride = stride // bytes_per_elem
                num_elems = (accessor["count"] - 1) * elems_per_stride + component_nb

                array = np.frombuffer(
                    buffer_data,
                    dtype=np.dtype(dtype).newbyteorder("<"),
                    count=num_elems,
                )
                assert array.strides[0] == bytes_per_elem
                array = np.lib.stride_tricks.as_strided(
                    array,
                    shape=(accessor["count"], component_nb),
                    strides=(stride, bytes_per_elem),
                )
        else:
            # No buffer view; initialize to zeros
            array = np.zeros((accessor.get("count"), component_nb), dtype=dtype)

        # Normalization
        if accessor.get("normalized"):
            if accessor["componentType"] == 5120:  # int8
                array = np.maximum(-1.0, array / 127.0)
            elif accessor["componentType"] == 5121:  # uint8
                array = array / 255.0
            elif accessor["componentType"] == 5122:  # int16
                array = np.maximum(-1.0, array / 32767.0)
            elif accessor["componentType"] == 5123:  # uint16
                array = array / 65535.0

            array = array.astype(np.float32, copy=False)

        return array
