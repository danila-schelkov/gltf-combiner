import numpy as np

from gltf_combiner.extensions.odin.attribute_format import OdinAttributeFormat
from gltf_combiner.extensions.odin.attribute_type import OdinAttributeType


class OdinAttribute:
    def __init__(
        self,
        attribute_type: OdinAttributeType,
        attribute_format: OdinAttributeFormat,
        offset: int,
    ) -> None:
        self.type = attribute_type
        self.format = attribute_format
        self.offset = offset

        self._dtype = OdinAttributeFormat.to_numpy_dtype(self.format)
        self._elements_count = OdinAttributeFormat.to_element_count(self.format)

    @property
    def data_type(self) -> np.dtype:
        return self._dtype

    @property
    def elements_count(self) -> int:
        return self._elements_count

    def read(self, data: bytes, offset: int) -> np.array:
        match self.format:
            case OdinAttributeFormat.NormalizedWeightVector:
                value = np.frombuffer(data, dtype=np.uint32, offset=offset, count=1)[0]
                x = (value >> 21) * 0.0002442
                y = ((value >> 10) & 0x7FF) * 0.0002442
                z = (value & 0x3FF) * 0.0002442
                array = np.array([((1.0 - x) - y) - z, x, y, z], dtype=self._dtype)
            case _:
                array = np.frombuffer(
                    data, dtype=self._dtype, offset=offset, count=self._elements_count
                )

        return array
