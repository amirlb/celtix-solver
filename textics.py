from collections import defaultdict
import csv

from common import *


def parse_csv_puzzle(f):
    rows = [[x.strip().lower() for x in row] for row in csv.reader(f)]
    assert rows[0][0] == 'celtix'
    width, height = map(int, rows[0][1:])
    pips = defaultdict(list)
    for color, x, y in rows[1:]:
        pips[color].append((int(x), int(y)))
    return Puzzle(width, height, dict(pips))

def print_solution(solution):
    print(f"Solved with {len(solution)} walls:")
    for wall in solution:
        print(f"{wall.x},{wall.y},{wall.orientation.name}")
