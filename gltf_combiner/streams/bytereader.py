from io import BufferedReader, BytesIO
from struct import unpack
from typing import Literal

from .common import get_endian_sign


class ByteReader:
    def __init__(self, initial_bytes: bytes, endian: Literal["big", "little"] = "big"):
        # noinspection PyTypeChecker
        self._internal_reader = BufferedReader(BytesIO(initial_bytes))
        self._endian_sign = get_endian_sign(endian)

    def seek(self, position: int) -> None:
        self._internal_reader.seek(position)

    def read(self, size: int) -> bytes:
        return self._internal_reader.read(size)

    def read_u_int64(self) -> int:
        return unpack(f"{self._endian_sign}Q", self.read(8))[0]

    def read_int64(self) -> int:
        return unpack(f"{self._endian_sign}q", self.read(8))[0]

    def read_u_int32(self) -> int:
        return unpack(f"{self._endian_sign}I", self.read(4))[0]

    def read_int32(self) -> int:
        return unpack(f"{self._endian_sign}i", self.read(4))[0]

    def read_u_int16(self) -> int:
        return unpack(f"{self._endian_sign}H", self.read(2))[0]

    def read_int16(self) -> int:
        return unpack(f"{self._endian_sign}h", self.read(2))[0]

    def read_u_int8(self) -> int:
        return unpack(f"{self._endian_sign}B", self.read(1))[0]

    def read_int8(self) -> int:
        return unpack(f"{self._endian_sign}b", self.read(1))[0]

    def read_string(self) -> str:
        length = self.read_int32()
        if length == -1:
            return ""

        return self.read(length).decode("utf-8")
