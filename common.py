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
        return f"Celtix puzzle, size {self.width}x{self.height}\n" + pips_str

    @property
    def n_colors(self):
        return len(self.pips)

    def cross_positions(self):
        # Ribbons cross at positions (x+0.5, y+0.5)
        for x in range(self.width - 1):
            for y in range((x + 1) % 2, self.height - 1, 2):
                yield (x, y)

    def edge_connections(self):
        # Pairs of connected points on the ribons, along the frame of the design
        for x in [0, self.width - 1]:
            for y in range(0, self.height, 2):
                yield ((x, y), (x, y+1))
        for y in [0, self.height - 1]:
            for x in range(0, self.width, 2):
                yield ((x, y), (x+1, y))

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

    def apply(self, x, y):
        return (round(self.x_transform.apply(x)), round(self.y_transform.apply(y)))
