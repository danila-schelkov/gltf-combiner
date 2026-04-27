from typing import Literal, assert_never

type EndianName = Literal["big", "little"]
type EndianSign = Literal[">", "<"]


def get_endian_sign(endian: EndianName) -> EndianSign:
    match endian:
        case "big":
            return ">"
        case "little":
            return "<"
        case _:
            assert_never(endian)
