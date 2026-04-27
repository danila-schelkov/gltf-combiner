from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..odin import SupercellOdinGLTF

from ._continuous_packed_reader import OdinContinuousPackedReader
from ._packed_reader import OdinPackedReader
from ._raw_reader import OdinRawAnimationReader
from ._reader import OdinAnimationReader


def create_reader(gltf: "SupercellOdinGLTF", descriptor: dict) -> OdinAnimationReader:
    if descriptor.get("nodes") is not None and descriptor.get("accessor") is not None:
        return OdinRawAnimationReader(gltf, descriptor)

    if (packed := descriptor.get("packed")) is not None:
        if packed.get("uintAccessor") is not None:
            return OdinContinuousPackedReader(gltf, descriptor)

        return OdinPackedReader(gltf, descriptor)

    raise NotImplementedError("Unknown animation data")
