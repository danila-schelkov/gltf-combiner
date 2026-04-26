from enum import IntEnum

import numpy as np


class ComponentType(IntEnum):
    Byte = 5120
    UnsignedByte = 5121
    Short = 5122
    UnsignedShort = 5123
    UnsignedInt = 5125
    Float = 5126

    def to_type_code(self) -> str:
        # return self.to_numpy_dtype().char
        return {
            ComponentType.Byte: "b",
            ComponentType.UnsignedByte: "B",
            ComponentType.Short: "h",
            ComponentType.UnsignedShort: "H",
            ComponentType.UnsignedInt: "I",
            ComponentType.Float: "f",
        }[self]

    def to_numpy_dtype(self) -> np.dtype:
        return {
            ComponentType.Byte: np.int8,
            ComponentType.UnsignedByte: np.uint8,
            ComponentType.Short: np.int16,
            ComponentType.UnsignedShort: np.uint16,
            ComponentType.UnsignedInt: np.uint32,
            ComponentType.Float: np.float32,
        }[self]

    def get_size(self) -> int:
        return {
            ComponentType.Byte: 1,
            ComponentType.UnsignedByte: 1,
            ComponentType.Short: 2,
            ComponentType.UnsignedShort: 2,
            ComponentType.UnsignedInt: 4,
            ComponentType.Float: 4,
        }[self]
