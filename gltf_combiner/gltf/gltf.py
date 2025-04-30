import os
from io import BytesIO
from typing import Self

from gltf_combiner.gltf.chunk import Chunk
from gltf_combiner.gltf.exceptions.wrong_file_exception import WrongFileException

GLTF_HEADER_SIZE = 12

GLTF_MAGIC = b"glTF"
GLTF_VERSION = 2


def get_file_data(filepath: os.PathLike | str) -> bytes:
    with open(filepath, "rb") as file:
        file_data = file.read()
        return file_data


def write_file_data(filepath: os.PathLike | str, data: bytes):
    with open(filepath, "wb") as file:
        file.write(data)


def is_at_end(buffer: BytesIO) -> bool:
    return buffer.tell() >= len(buffer.getvalue())


class GlTF:
    def __init__(self, *chunks: Chunk):
        self._file_read_buffer = BytesIO()
        self._file_write_buffer = BytesIO()

        self._chunks: list[Chunk] = list(chunks)

    @staticmethod
    def parse(filepath: os.PathLike | str) -> "GlTF":
        gltf = GlTF()

        file_data = get_file_data(filepath)
        file_length = len(file_data)
        gltf._file_read_buffer = BytesIO(file_data)

        if gltf._validate(file_length):
            raise WrongFileException("File is not validated!")

        gltf._chunks = gltf._parse_chunks()
        assert is_at_end(gltf._file_read_buffer), "Cannot parse whole file."

        return gltf

    def write(self, filepath: os.PathLike | str) -> Self:
        self._file_write_buffer = BytesIO()

        chunks_buffer = self._write_chunks()

        self._file_write_buffer.write(GLTF_MAGIC)
        self._file_write_buffer.write(int.to_bytes(GLTF_VERSION, 4, "little"))
        self._file_write_buffer.write(
            int.to_bytes(len(chunks_buffer.getvalue()) + GLTF_HEADER_SIZE, 4, "little")
        )

        self._file_write_buffer.write(chunks_buffer.getvalue())

        write_file_data(filepath, self._file_write_buffer.getvalue())

        return self

    def get_chunk_by_type(self, chunk_type: bytes) -> Chunk | None:
        for chunk in self._chunks:
            if chunk.type == chunk_type:
                return chunk

        return None

    def add_chunk(self, new_chunk: Chunk) -> Chunk:
        for chunk in self._chunks:
            if chunk.type == new_chunk.type:
                self._chunks.remove(chunk)
                break

        self._chunks.append(new_chunk)
        return new_chunk

    def _validate(self, file_length: int) -> bool:
        magic = self._file_read_buffer.read(4)
        if magic != b"glTF":
            return True

        version = int.from_bytes(self._file_read_buffer.read(4), "little")
        if version != 2:
            return True

        length = int.from_bytes(self._file_read_buffer.read(4), "little")
        if length != file_length:
            return True

        return False

    def _parse_chunks(self) -> list[Chunk]:
        chunks = []

        while not is_at_end(self._file_read_buffer):
            chunk_length = int.from_bytes(self._file_read_buffer.read(4), "little")
            chunk_type = self._file_read_buffer.read(4)
            chunk_data = self._file_read_buffer.read(chunk_length)

            chunks.append(Chunk(type=chunk_type, data=chunk_data))

        return chunks

    def _write_chunks(self) -> BytesIO:
        io = BytesIO()

        for chunk in self._chunks:
            io.write(int.to_bytes(len(chunk), 4, "little"))
            io.write(chunk.type)
            io.write(chunk.data)

        return io
