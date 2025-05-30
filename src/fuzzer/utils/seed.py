from typing import Union, Tuple


class Seed:
    """Represent an input with additional attributes"""

    def __init__(self, data: Tuple[str, str]) -> None:
        """Initialize from seed data"""
        self.data = data
        self.path_id: str = ""
        self.distance: Union[int, float] = -1
        self.energy = 0.0

    def __str__(self) -> Tuple[str, str]:
        """Returns data as string representation of the seed"""
        return self.data
