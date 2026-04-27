class OdinAnimationFlags:
    def __init__(self, flags: int = 0) -> None:
        self.flags: int = flags

    @property
    def has_transform(self) -> bool:
        return self.flags != 0

    @property
    def has_frametime(self) -> bool:
        return self.flags & 1 != 0

    @property
    def has_rotation(self) -> bool:
        return self.flags & 2 != 0

    @property
    def has_translation(self) -> bool:
        return self.flags & 4 != 0

    @property
    def has_scale(self) -> bool:
        return self.flags & 8 != 0

    @property
    def has_separate_scale(self) -> bool:
        return self.flags & 16 != 0

    @property
    def element_count(self) -> int:
        result = 0
        if self.has_frametime:
            result += 1
        if self.has_rotation:
            result += 4
        if self.has_translation:
            result += 3
        if self.has_separate_scale and self.has_scale:
            result += 3
        elif self.has_scale:
            result += 1

        return result
