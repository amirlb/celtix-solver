from dataclasses import dataclass
import cv2 as cv
import numpy as np

from common import *


@dataclass
class Rectangle:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def area(self):
        return (self.x2 - self.x1 + 1) * (self.y2 - self.y1 + 1)

    @property
    def perimeter(self):
        return 2 * (self.x2 - self.x1 + self.y2 - self.y1)

def find_board(edges):
    n_rows, n_cols = edges.shape
    # precompute for the calculations ahead
    row_cumsums = np.array([np.cumsum(edges[row]) for row in range(n_rows)])
    col_cumsums = np.array([np.cumsum(edges[:,col]) for col in range(n_cols)])
    # rows and columns with 50 out of 100 on
    strong_rows = [row for row, cc in enumerate(row_cumsums) if np.any(cc[100:] - cc[:-100] > 50)]
    strong_cols = [col for col, cc in enumerate(col_cumsums) if np.any(cc[100:] - cc[:-100] > 50)]
    rects = [
        Rectangle(x1, y1, x2, y2)
        for x1 in strong_cols for x2 in strong_cols
        if x1 + 10 < x2
        for y1 in strong_rows for y2 in strong_rows
        if y1 + 10 < y2
    ]
    def border_frac(rect):
        border = (
            row_cumsums[rect.y1][rect.x2+1] - row_cumsums[rect.y1][rect.x1] +
            row_cumsums[rect.y2][rect.x2+1] - row_cumsums[rect.y2][rect.x1] +
            col_cumsums[rect.x1][rect.y2+1] - col_cumsums[rect.x1][rect.y1] +
            col_cumsums[rect.x2][rect.y2+1] - col_cumsums[rect.x2][rect.y1]
        )
        return border / rect.perimeter
    def has_spaces(rect):
        empty_rows = np.any(row_cumsums[rect.y1:rect.y2, rect.x2] == row_cumsums[rect.y1:rect.y2, rect.x1])
        empty_cols = np.any(col_cumsums[rect.x1:rect.x2, rect.y2] == col_cumsums[rect.x1:rect.x2, rect.y1])
        return empty_rows or empty_cols
    return max(
        [rect for rect in rects if border_frac(rect) > 0.5 and not has_spaces(rect)],
        key=lambda rect: rect.area
    )

def correlation_distance(values, min_dist=10):
    n = len(values)
    scores = [
        np.sum((values[:n//2] - values[dist : dist+n//2]) ** 2)
        for dist in range(min_dist, n//2)
    ]
    threshold = min(scores) ** 0.75 * max(scores) ** 0.25
    return next(dist + min_dist for dist, score in enumerate(scores) if score < threshold)

def sum_diagonals(arr):
    rows, cols = arr.shape
    k = min(rows // 2, cols)
    return np.sum([arr[i : i + k, i] for i in range(k)], axis=0)

def build_transform(start, end, count):
    slope = (end - start) / count
    intercept = start + 0.5 * slope
    return LinearTransform(intercept, slope)

def find_grid(edges, rect):
    corr = correlation_distance(sum_diagonals(edges[rect.y1:rect.y2, rect.x1:rect.x2]))
    width = 2 * round((rect.x2 - rect.x1) / corr)
    height = 2 * round((rect.y2 - rect.y1) / corr)
    grid = Grid(
        x_transform=build_transform(rect.x1, rect.x2, width),
        y_transform=build_transform(rect.y1, rect.y2, height),
    )
    return width, height, grid

@dataclass
class ColorGroup:
    canonical: np.ndarray
    variations: list[tuple[int, int, int]]

    @classmethod
    def create(cls, color):
        return cls(np.array(color, dtype=float), [color])

    def contains(self, color):
        return np.sum((self.canonical - color) ** 2) < 100

    def best_name(self):
        avg_color = np.mean(self.variations, axis=0)
        return "color_{2:02x}{1:02x}{0:02x}".format(*map(round, avg_color))

def non_common_colors(colors):
    groups = []
    for color in colors:
        for group in groups:
            if group.contains(color):
                group.variations.append(color)
                break
        else:
            groups.append(ColorGroup.create(color))
    return {
        variation: group.best_name()
        for group in groups if len(group.variations) < 10
        for variation in group.variations
    }

def parse_image(image):
    image = cv.GaussianBlur(image, (5, 5), 0)
    edges = cv.Canny(
        cv.cvtColor(image, cv.COLOR_BGR2GRAY),
        50, 100,
        apertureSize=5, L2gradient=True,
    ).astype(int) // 255
    rect = find_board(edges)
    width, height, grid = find_grid(edges, rect)
    colors = {
        (x, y): tuple(image[grid.apply(x, y)[::-1]])
        for x in range(width) for y in range(height)
    }
    pip_colors = non_common_colors(colors.values())
    pips = {
        color_name: [pt for pt, color in colors.items() if pip_colors.get(color) == color_name]
        for color_name in set(pip_colors.values())
    }
    return Puzzle(width, height, pips), grid

def to_faded_grayscale(image):
    # There's got to be a better way...
    output = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    output = cv.cvtColor(output, cv.COLOR_GRAY2BGR)
    return cv.convertScaleAbs(output, alpha=0.5, beta=128)

def draw_solution(image, grid, solution):
    output = to_faded_grayscale(image)
    for wall in solution:
        if wall.orientation == Orientation.horizontal:
            dx, dy = 0.3, 0.0
        else:
            dx, dy = 0.0, 0.3
        x1, y1 = grid.apply(wall.x + 0.5 - dx, wall.y + 0.5 - dy)
        x2, y2 = grid.apply(wall.x + 0.5 + dx, wall.y + 0.5 + dy)
        cv.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
    return output
