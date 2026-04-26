from enum import IntEnum

import numpy as np

from gltf_combiner.extensions.odin.gltf_data_type import DataType


class OdinAttributeFormat(IntEnum):
    UByteVector4 = 3
    ColorRGBA = 9
    UByteVector3 = 12
    FloatVector2 = 29
    FloatVector3 = 30
    NormalizedWeightVector = 36

    def is_normalized(self) -> bool:
        return {
            OdinAttributeFormat.FloatVector3: False,
            OdinAttributeFormat.UByteVector3: False,
            OdinAttributeFormat.UByteVector4: False,
            OdinAttributeFormat.NormalizedWeightVector: False,
            OdinAttributeFormat.FloatVector2: False,
            OdinAttributeFormat.ColorRGBA: True,
        }[self]

    def to_accessor_type(self) -> DataType:
        return {
            OdinAttributeFormat.FloatVector3: DataType.Vec3,
            OdinAttributeFormat.UByteVector3: DataType.Vec3,
            OdinAttributeFormat.UByteVector4: DataType.Vec4,
            OdinAttributeFormat.NormalizedWeightVector: DataType.Vec4,
            OdinAttributeFormat.FloatVector2: DataType.Vec2,
            OdinAttributeFormat.ColorRGBA: DataType.Vec4,
        }[self]

    def to_accessor_component(self) -> int:
        return {
            OdinAttributeFormat.FloatVector3: 5126,
            OdinAttributeFormat.UByteVector3: 5120,
            OdinAttributeFormat.UByteVector4: 5121,
            OdinAttributeFormat.NormalizedWeightVector: 5126,
            OdinAttributeFormat.FloatVector2: 5126,
            OdinAttributeFormat.ColorRGBA: 5121,
        }[self]

    def to_numpy_dtype(self) -> np.dtype:
        return {
            OdinAttributeFormat.FloatVector3: np.uint32,
            OdinAttributeFormat.UByteVector3: np.byte,
            OdinAttributeFormat.UByteVector4: np.ubyte,
            OdinAttributeFormat.NormalizedWeightVector: np.float32,
            OdinAttributeFormat.FloatVector2: np.float32,
            OdinAttributeFormat.ColorRGBA: np.ubyte,
        }[self]

    def to_element_count(self) -> int:
        return {
            OdinAttributeFormat.FloatVector3: 3,
            OdinAttributeFormat.UByteVector3: 3,
            OdinAttributeFormat.UByteVector4: 4,
            OdinAttributeFormat.NormalizedWeightVector: 4,
            OdinAttributeFormat.FloatVector2: 2,
            OdinAttributeFormat.ColorRGBA: 4,
        }[self]
