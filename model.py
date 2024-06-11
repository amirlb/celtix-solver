import mip
import networkx as nx

def get_matches(x, y, d):
    if d == 'H':
        return [((x, y), (x+1, y)), ((x, y+1), (x+1, y+1))]
    elif d == 'V':
        return [((x, y), (x, y+1)), ((x+1, y), (x+1, y+1))]
    else:
        return [((x, y), (x+1, y+1)), ((x, y+1), (x+1, y))]

def build_base_model(width, height, n_colors):
    print(f"Building {width}x{height} model with {n_colors} colors")
    m = mip.Model("celtix")
    color_vars = [
        [
            [
                m.add_var(var_type=mip.BINARY)
                for _ in range(n_colors)
            ]
            for _ in range(height)
        ]
        for _ in range(width)
    ]
    for x in range(width):
        for y in range(height):
            m += mip.xsum(color_vars[x][y]) == 1
    for x in [0, width - 1]:
        for y in range(0, height, 2):
            for c in range(n_colors):
                m += color_vars[x][y][c] - color_vars[x][y+1][c] == 0
    for y in [0, height - 1]:
        for x in range(0, width, 2):
            for c in range(n_colors):
                m += color_vars[x][y][c] - color_vars[x+1][y][c] == 0
    cross_vars, all_cross_vars = [], []
    for x in range(width - 1):
        cross_vars.append([[] for _ in range(height)])
        for y in range((x + 1) % 2, height - 1, 2):
            # cross between [x:x+1] and [y:y+1]
            h = m.add_var(var_type=mip.BINARY)
            v = m.add_var(var_type=mip.BINARY)
            m += h + v <= 1
            cross_vars[x][y] = [h, v]
            all_cross_vars.extend([h, v])
            for c in range(n_colors):
                for (x1, y1), (x2, y2) in get_matches(x, y, 'H'):
                    m += color_vars[x1][y1][c] - color_vars[x2][y2][c] <= 1 - h
                    m += color_vars[x2][y2][c] - color_vars[x1][y1][c] <= 1 - h
                for (x1, y1), (x2, y2) in get_matches(x, y, 'V'):
                    m += color_vars[x1][y1][c] - color_vars[x2][y2][c] <= 1 - v
                    m += color_vars[x2][y2][c] - color_vars[x1][y1][c] <= 1 - v
                for (x1, y1), (x2, y2) in get_matches(x, y, ''):
                    m += color_vars[x1][y1][c] - color_vars[x2][y2][c] <= h + v
                    m += color_vars[x2][y2][c] - color_vars[x1][y1][c] <= h + v
    m.objective = mip.minimize(mip.xsum(all_cross_vars))
    return m, color_vars, cross_vars

def build_model(coords_by_color, width, height):
    n_colors = len(coords_by_color)
    m, color_vars, cross_vars = build_base_model(width, height, n_colors)
    for c, coords in enumerate(coords_by_color.values()):
        for x, y in coords:
            m += color_vars[x][y][c] == 1
    return m, cross_vars

def find_loops(width, height, walls):
    G = nx.Graph()
    for x in range(width):
        for y in range(height):
            G.add_node((x, y))
    for x in [0, width - 1]:
        for y in range(0, height, 2):
            G.add_edge((x, y), (x, y+1))
    for y in [0, height - 1]:
        for x in range(0, width, 2):
            G.add_edge((x, y), (x+1, y))
    walls_dict = {(x, y): d for x, y, d in walls}
    for x in range(width - 1):
        for y in range((x + 1) % 2, height - 1, 2):
            G.add_edges_from(get_matches(x, y, walls_dict.get((x, y), '')))
    return [set(component) for component in nx.connected_components(G)]

def anti_loop_constraint(cross_vars, loop):
    anti_loop = []
    for x, col_vars in enumerate(cross_vars):
        for y, vars in enumerate(col_vars):
            if vars:
                if vars[0].x >= 0.99 and any(all(pt in loop for pt in pair) for pair in get_matches(x, y, 'H')):
                    anti_loop.append(1 - vars[0])
                if vars[1].x >= 0.99 and any(all(pt in loop for pt in pair) for pair in get_matches(x, y, 'V')):
                    anti_loop.append(1 - vars[1])
                if vars[0].x <= 0.01 and vars[1].x <= 0.01 and any(all(pt in loop for pt in pair) for pair in get_matches(x, y, '')):
                    anti_loop.append(vars[0] + vars[1])
    return mip.xsum(anti_loop) >= 1

def solve_puzzle(coords_by_color):
    width = 1 + max(x for coords in coords_by_color.values() for x, _ in coords)
    if width % 2 == 1:
        width += 1
    height = 1 + max(y for coords in coords_by_color.values() for _, y in coords)
    if height % 2 == 1:
        height += 1

    m, cross_vars = build_model(coords_by_color, width, height)
    while True:
        print("Solving model")
        m.optimize()

        walls = []
        for x, col in enumerate(cross_vars):
            for y, vars in enumerate(col):
                if vars:
                    if vars[0].x >= 0.99:
                        walls.append((x, y, 'H'))
                    if vars[1].x >= 0.99:
                        walls.append((x, y, 'V'))
        print(f"Tentative solution with {len(walls)} walls")

        loops = find_loops(width, height, walls)
        if len(loops) == len(coords_by_color):
            return walls

        loops_by_color = {color: [] for color in coords_by_color.keys()}
        for loop in loops:
            for color, coords in coords_by_color.items():
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
