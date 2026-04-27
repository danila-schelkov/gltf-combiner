from typing import Literal


def get_endian_sign(endian: Literal["big", "little"]) -> Literal[">", "<"]:
    if endian == "big":
        return ">"
    elif endian == "little":
        return "<"

    raise NotImplementedError(f"Unknown endian requested: {endian}")
