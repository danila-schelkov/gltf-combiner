from typing import Literal, TypeAlias, assert_never

EndianName: TypeAlias = Literal["big", "little"]
EndianSign: TypeAlias = Literal[">", "<"]


def get_endian_sign(endian: EndianName) -> EndianSign:
    match endian:
        case "big":
            return ">"
        case "little":
            return "<"
        case _:
            assert_never(endian)
