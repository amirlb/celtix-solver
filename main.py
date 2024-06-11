import sys

from model import solve_puzzle
from vision import detect_pips
import cv2 as cv


image_path = sys.argv[1]
coords_by_color, output, ax, bx, ay, by = detect_pips(image_path)
for k, v in coords_by_color.items():
    print(f"{str(k):20} {v}")
solution = solve_puzzle(coords_by_color)
for x, y, direction in solution:
    if direction == 'H':
        print(f"Horizontal wall at {x}.5,{y}.5")
        start = (round(ax + (x + 0.2) * bx), round(ay + (y + 0.5) * by))
        end = (round(ax + (x + 0.8) * bx), round(ay + (y + 0.5) * by))
    else:
        print(f"Vertical wall at {x}.5,{y}.5")
        start = (round(ax + (x + 0.5) * bx), round(ay + (y + 0.2) * by))
        end = (round(ax + (x + 0.5) * bx), round(ay + (y + 0.8) * by))
    cv.line(output, start, end, (0, 0, 255), 3)
cv.imwrite("output.png", output)
