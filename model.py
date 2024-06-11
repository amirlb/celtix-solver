import mip

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
                # if h      (x,y)=(x+1,y)   (x,y+1)=(x+1,y+1)
                m += color_vars[x][y][c] - color_vars[x+1][y][c] <= 1 - h
                m += color_vars[x+1][y][c] - color_vars[x][y][c] <= 1 - h
                m += color_vars[x][y+1][c] - color_vars[x+1][y+1][c] <= 1 - h
                m += color_vars[x+1][y+1][c] - color_vars[x][y+1][c] <= 1 - h
                # if v      (x,y)=(x,y+1)   (x+1,y)=(x+1,y+1)
                m += color_vars[x][y][c] - color_vars[x][y+1][c] <= 1 - v
                m += color_vars[x][y+1][c] - color_vars[x][y][c] <= 1 - v
                m += color_vars[x+1][y][c] - color_vars[x+1][y+1][c] <= 1 - v
                m += color_vars[x+1][y+1][c] - color_vars[x+1][y][c] <= 1 - v
                # if 1-h-v  (x,y)=(x+1,y+1) (x,y+1)=(x+1,y)
                m += color_vars[x][y][c] - color_vars[x+1][y+1][c] <= h + v
                m += color_vars[x+1][y+1][c] - color_vars[x][y][c] <= h + v
                m += color_vars[x+1][y][c] - color_vars[x][y+1][c] <= h + v
                m += color_vars[x][y+1][c] - color_vars[x+1][y][c] <= h + v
    # TODO: add row-generation constraint that there are only n_colors cycles
    m.objective = mip.minimize(mip.xsum(all_cross_vars))
    return m, color_vars, cross_vars

def build_model(coords_by_color):
    n_colors = len(coords_by_color)
    width = 1 + max(x for coords in coords_by_color.values() for x, _ in coords)
    if width % 2 == 1:
        width += 1
    height = 1 + max(y for coords in coords_by_color.values() for _, y in coords)
    if height % 2 == 1:
        height += 1
    m, color_vars, cross_vars = build_base_model(width, height, n_colors)
    for c, coords in enumerate(coords_by_color.values()):
        for x, y in coords:
            m += color_vars[x][y][c] == 1
    return m, cross_vars

def solve_puzzle(coords_by_color):
    m, cross_vars = build_model(coords_by_color)
    print("Solving model")
    m.optimize()
    bars = []
    for x, col in enumerate(cross_vars):
        for y, vars in enumerate(col):
            if vars:
                if vars[0].x >= 0.99:
                    print(f"Horizontal bar at {x}.5,{y}.5")
                    bars.append((x, y, 'H'))
                if vars[1].x >= 0.99:
                    print(f"Vertical bar at {x}.5,{y}.5")
                    bars.append((x, y, 'V'))
    return bars
