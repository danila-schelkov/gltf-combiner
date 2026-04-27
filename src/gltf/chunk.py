from dataclasses import dataclass
from typing import Any

import orjson


@dataclass
class Chunk:
    type: bytes
    data: bytes

    def json(self) -> dict[str, Any]:
        return orjson.loads(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"Chunk(type={self.type})"
