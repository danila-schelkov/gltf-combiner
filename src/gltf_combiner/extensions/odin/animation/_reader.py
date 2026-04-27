import abc


class OdinAnimationReader(abc.ABC):
    def __init__(self, animation: dict) -> None:
        self.frame_rate: int = animation.get("frameRate") or 30
        self.frame_spf: float = 1.0 / self.frame_rate
        self.keyframe_count: int = (
            animation.get("keyframesCount") or animation.get("keyframeCount")
        ) or 1
        self.nodes_per_keyframe: int = animation.get("nodesNumberPerKeyframe")
        self.keyframe_mapping: list[int] | None = None
        self.used_nodes: list[int] = []

    @abc.abstractmethod
    def read(self) -> None:
        """Reads buffer data"""

    @classmethod
    @abc.abstractmethod
    def get_frame_data(
        cls, node_index: int, frame_index: int
    ) -> tuple[list[float], list[float], list[float]]:
        """Returns frame data for specific node in format (Translation, Rotation, Scale)"""
