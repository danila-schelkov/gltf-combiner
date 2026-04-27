import orjson
from dataclasses import dataclass


@dataclass
class Chunk:
    type: bytes
    data: bytes

    def json(self) -> dict:
        return orjson.loads(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"Chunk(type={self.type})"
