from enum import IntEnum
from typing import Self


class OdinAttributeType(IntEnum):
    a_pos = 0
    a_normal = 1
    a_uv0 = 2
    a_uv1 = 3
    a_color = 4
    a_boneindex = 5
    a_boneweights = 6
    a_tangent = 7
    a_colorMul = 8
    a_colorAdd = 9
    a_model = 10
    a_model2 = 11
    a_model3 = 12
    a_binormal = 13
    a_skinningOffsets = 14
    a_color1 = 15

    @classmethod
    def to_attribute_name(cls, component_type: Self) -> str:
        return {
            OdinAttributeType.a_pos: "POSITION",
            OdinAttributeType.a_normal: "NORMAL",
            OdinAttributeType.a_boneindex: "JOINTS_0",
            OdinAttributeType.a_boneweights: "WEIGHTS_0",
            OdinAttributeType.a_uv0: "TEXCOORD_0",
            OdinAttributeType.a_uv1: "TEXCOORD_1",
            OdinAttributeType.a_color: "COLOR_0",
            OdinAttributeType.a_color1: "COLOR_1",
        }[component_type]
