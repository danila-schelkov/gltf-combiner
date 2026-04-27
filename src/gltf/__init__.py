from .chunk import Chunk
from .gltf import GlTF

__all__ = [
    "GlTF",
    "Chunk",
    "JSON_CHUNK_TYPE",
    "FLATBUFFER_CHUNK_TYPE",
    "BIN_CHUNK_TYPE",
]

JSON_CHUNK_TYPE: bytes = b"JSON"
FLATBUFFER_CHUNK_TYPE: bytes = b"FLA2"
BIN_CHUNK_TYPE: bytes = b"BIN\0"
