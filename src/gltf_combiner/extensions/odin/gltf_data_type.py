from enum import StrEnum


class DataType(StrEnum):
    Scalar = "SCALAR"
    Vec2 = "VEC2"
    Vec3 = "VEC3"
    Vec4 = "VEC4"
    Mat2 = "MAT2"
    Mat3 = "MAT3"
    Mat4 = "MAT4"

    def num_elements(self) -> int:
        return {
            DataType.Scalar: 1,
            DataType.Vec2: 2,
            DataType.Vec3: 3,
            DataType.Vec4: 4,
            DataType.Mat2: 4,
            DataType.Mat3: 9,
            DataType.Mat4: 16,
        }[self]

    @classmethod
    def vec_type_from_num(cls, num_elems: int):
        if not (0 < num_elems < 5):
            raise ValueError(f"No vector type with {num_elems} elements")
        return {
            1: DataType.Scalar,
            2: DataType.Vec2,
            3: DataType.Vec3,
            4: DataType.Vec4,
        }[num_elems]

    @classmethod
    def mat_type_from_num(cls, num_elems: int):
        if not (4 <= num_elems <= 16):
            raise ValueError(f"No matrix type with {num_elems} elements")
        return {4: DataType.Mat2, 9: DataType.Mat3, 16: DataType.Mat4}[num_elems]
