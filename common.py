from dataclasses import dataclass
from enum import Enum, auto


ColorName = str
Point = tuple[int, int]

@dataclass
class Puzzle:
    width: int
    height: int
    pips: dict[ColorName, list[Point]]

    def __str__(self):
        pips_str = "\n".join(f"  {color}: {pts}" for color, pts in self.pips.items())
        return f"Cetrix puzzle, size {self.width}x{self.height}\n" + pips_str

class Orientation(Enum):
    horizontal = auto()
    vertical = auto()

@dataclass
class Wall:
    x: int
    y: int
    orientation: Orientation

Solution = list[Wall]

@dataclass
class LinearTransform:
    intercept: float
    slope: float

    def apply(self, x):
        return self.intercept + x * self.slope

@dataclass
class Grid:
    x_transform: LinearTransform
    y_transform: LinearTransform
