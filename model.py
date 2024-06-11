import mip
import networkx as nx

from common import *


def get_matches(x, y, orientation):
    if orientation == Orientation.horizontal:
        return [((x, y), (x+1, y)), ((x, y+1), (x+1, y+1))]
    elif orientation == Orientation.vertical:
        return [((x, y), (x, y+1)), ((x+1, y), (x+1, y+1))]
    else:
        return [((x, y), (x+1, y+1)), ((x, y+1), (x+1, y))]

def build_model(puzzle):
    m = mip.Model("Celtix")

    # Indicators for color[x, y] == c
    color_vars = {
        (x, y): [m.add_var(var_type=mip.BINARY) for _ in range(puzzle.n_colors)]
        for x in range(puzzle.width)
        for y in range(puzzle.height)
    }
    # Horizontal and vertical variables for each position
    cross_vars = {
        (x, y): [m.add_var(var_type=mip.BINARY), m.add_var(var_type=mip.BINARY)]
        for x, y in puzzle.cross_positions()
    }

    # Each position has a (single) color
    for x in range(puzzle.width):
        for y in range(puzzle.height):
            m += mip.xsum(color_vars[x, y]) == 1

    # Ribbons are connected along the edges
    for (x1, y1), (x2, y2) in puzzle.edge_connections():
        for c in range(puzzle.n_colors):
            m += color_vars[x1, y1][c] - color_vars[x2, y2][c] == 0

    # Connections at crossing points
    for (x, y), (h, v) in cross_vars.items():
        for c in range(puzzle.n_colors):
            for (x1, y1), (x2, y2) in get_matches(x, y, Orientation.horizontal):
                m += color_vars[x1, y1][c] - color_vars[x2, y2][c] <= 1 - h
                m += color_vars[x2, y2][c] - color_vars[x1, y1][c] <= 1 - h
            for (x1, y1), (x2, y2) in get_matches(x, y, Orientation.vertical):
                m += color_vars[x1, y1][c] - color_vars[x2, y2][c] <= 1 - v
                m += color_vars[x2, y2][c] - color_vars[x1, y1][c] <= 1 - v
            for (x1, y1), (x2, y2) in get_matches(x, y, None):
                m += color_vars[x1, y1][c] - color_vars[x2, y2][c] <= h + v
                m += color_vars[x2, y2][c] - color_vars[x1, y1][c] <= h + v

    # The ribbon under each pip has the pip's color
    for c, pts in enumerate(puzzle.pips.values()):
        for x, y in pts:
            m += color_vars[x, y][c] == 1

    # Try to get as few walls as possible
    num_walls = mip.xsum(var for vars in cross_vars.values() for var in vars)
    m.objective = mip.minimize(num_walls)

    return m, cross_vars

def find_loops(puzzle, walls):
    # Build the connectivity between ribbon segments
    G = nx.Graph()
    G.add_nodes_from((x, y) for x in range(puzzle.width) for y in range(puzzle.height))
    G.add_edges_from(puzzle.edge_connections())
    for x, y in puzzle.cross_positions():
        G.add_edges_from(get_matches(x, y, walls.get((x, y))))
    # Ribbon loops are connected components of that graph
    return [set(component) for component in nx.connected_components(G)]

def anti_loop_constraint(cross_vars, loop):
    # Collect expressions that would contradict the crossing decisions made before
    anti_loop = []
    for (x, y), (h, v) in cross_vars.items():
        if h.x >= 0.99 and any(loop.issuperset(pair) for pair in get_matches(x, y, Orientation.horizontal)):
            anti_loop.append(1 - h)
        if v.x >= 0.99 and any(loop.issuperset(pair) for pair in get_matches(x, y, Orientation.vertical)):
            anti_loop.append(1 - v)
        if h.x <= 0.01 and v.x <= 0.01 and any(loop.issuperset(pair) for pair in get_matches(x, y, None)):
            anti_loop.append(h + v)
    # The new constraint requires at least one contradiction to the loop
    return mip.xsum(anti_loop) >= 1

def solve_puzzle(puzzle):
    m, cross_vars = build_model(puzzle)
    while True:
        print("Solving model")
        m.optimize()

        walls = {}
        for (x, y), (h, v) in cross_vars.items():
            if h.x >= 0.99:
                walls[(x, y)] = Orientation.horizontal
            if v.x >= 0.99:
                walls[(x, y)] = Orientation.vertical
        print(f"Tentative solution with {len(walls)} walls")

        loops = find_loops(puzzle, walls)
        if len(loops) == puzzle.n_colors:
            return [Wall(x, y, orientation) for (x, y), orientation in walls.items()]

        loops_by_color = {color: [] for color in puzzle.pips.keys()}
        for loop in loops:
            for color, coords in puzzle.pips.items():
                if any(coord in loop for coord in coords):
                    loops_by_color[color].append(loop)
                    break
            else:
                print(f"Adding constraint against uncolored loop", loop)
                m += anti_loop_constraint(cross_vars, loop)
        for color, color_loops in loops_by_color.items():
            if len(color_loops) > 1:
                for loop in color_loops:
                    print(f"Adding constraint against", color, "loop", loop)
                    m += anti_loop_constraint(cross_vars, loop)
