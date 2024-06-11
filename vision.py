from collections import defaultdict
import cv2 as cv
import numpy as np

def fix_coord(values):
    values = list(values)
    lo, hi = min(values), max(values)
    best = {'score': np.inf}
    for start in range(10):
        for end in range(start + 1, 30):
            b = (hi - lo) / (end - start)
            a = lo - start * b
            opts = a + np.arange(30) * b
            score = sum(np.min(np.abs(opts - v)) for v in values)
            if score < best['score']:
                best = {'score': score, 'a': a, 'b': b}
    opts = best['a'] + np.arange(30) * best['b']
    return [np.argmin(np.abs(opts - v)) for v in values], best['a'], best['b']

def detect_pips(filename):
    src = cv.imread(cv.samples.findFile(filename), cv.IMREAD_COLOR)
    gray = cv.cvtColor(src, cv.COLOR_BGR2GRAY)
    rows = src.shape[0]
    [circles] = cv.HoughCircles(
        gray,
        cv.HOUGH_GRADIENT, 1, rows / 50,
        param1=100, param2=20,
        minRadius=rows // 100, maxRadius=rows // 30,
    )
    x_coords, ax, bx = fix_coord([x for x, _, _ in circles])
    y_coords, ay, by = fix_coord([y for _, y, _ in circles])
    by_color = defaultdict(list)
    for (x, y, _), x_coord, y_coord in zip(circles, x_coords, y_coords):
        color = src[int(y), int(x)]
        color_tuple = tuple(map(int, color))
        by_color[color_tuple].append((x_coord, y_coord))
    return by_color, cv.cvtColor(gray, cv.COLOR_GRAY2BGR), ax, bx, ay, by
