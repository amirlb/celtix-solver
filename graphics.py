from collections import defaultdict
import cv2 as cv
import numpy as np

from common import *


def build_transform(x1, y1, x2, y2):
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - x1 * slope
    return LinearTransform(intercept, slope)

def infer_transform(values):
    # We have a list of locations, but they don't necessarily include the edges
    # Try out possible variations for what the lowest and highest seen are
    lo, hi = min(values), max(values)
    options = [
        build_transform(start, lo, end, hi)
        for start in range(2)
        for end in range(start + 8, 30)
    ]
    def score(transform):
        codomain = transform.intercept + np.arange(30) * transform.slope
        return sum(np.min(np.abs(codomain - v)) for v in values)

    return min(options, key=score)

def best_match(value, transform):
    codomain = transform.intercept + np.arange(30) * transform.slope
    return np.argmin(np.abs(codomain - value))

def parse_image(image):
    rows = image.shape[0]
    [circles] = cv.HoughCircles(
        cv.cvtColor(image, cv.COLOR_BGR2GRAY),
        cv.HOUGH_GRADIENT, 1, rows / 50,
        param1=100, param2=20,
        minRadius=rows // 100, maxRadius=rows // 30,
    )
    grid = Grid(
        x_transform=infer_transform([x for x, _, _ in circles]),
        y_transform=infer_transform([y for _, y, _ in circles]),
    )
    print(grid)
    pips = defaultdict(list)
    for x, y, _ in circles:
        pip_x = best_match(x, grid.x_transform)
        pip_y = best_match(y, grid.y_transform)
        color = image[round(y), round(x)]
        color_name = "color_{:02x}{:02x}{:02x}".format(*color)
        pips[color_name].append((pip_x, pip_y))
    width = max(x for lst in pips.values() for x, _ in lst)
    width += width % 2
    height = max(y for lst in pips.values() for _, y in lst)
    height += height % 2
    return Puzzle(width, height, dict(pips)), grid

def to_faded_grayscale(image):
    # There's got to be a better way...
    output = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    output = cv.cvtColor(output, cv.COLOR_GRAY2BGR)
    return cv.convertScaleAbs(output, alpha=0.5, beta=96)

def draw_solution(image, grid, solution):
    output = to_faded_grayscale(image)
    for wall in solution:
        if wall.orientation == Orientation.horizontal:
            dx, dy = 0.3, 0.0
        else:
            dx, dy = 0.0, 0.3
        x1 = round(grid.x_transform.apply(wall.x + 0.5 - dx))
        y1 = round(grid.y_transform.apply(wall.y + 0.5 - dy))
        x2 = round(grid.x_transform.apply(wall.x + 0.5 + dx))
        y2 = round(grid.y_transform.apply(wall.y + 0.5 + dy))
        cv.line(output, (x1, y1), (x2, y2), (0, 0, 255), 3)
    return output
