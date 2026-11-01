import random

"""
0 = empty, 1 = fresh_apple, 2 = rotten_apple
"""
estados = [0, 1, 2]

ancho = 4
alto = 5

def create_grid():
    grid = []
    for i in range(alto):
        row = []
        for j in range(ancho):
            row.append(random.choice(estados))
        grid.append(row)
    return grid

world = create_grid()
for row in world:
    print(row)

def rot_apples(grid, x, y):
    """
    horizontal change
    """
    if x > 0 and x < len(grid[0]) - 1:
        if grid[y][x] == 2:
            if grid[y][x-1] != 0:
                grid[y][x-1] = 2
            if grid[y][x+1] != 0:
                grid[y][x+1] = 2
    
    if x == 0:
        if grid[y][x] == 2:
            if grid[y][x+1] != 0:
                grid[y][x+1] = 2
                
    if x == len(grid[0]) - 1:
        if grid[y][x] == 2:
            if grid[y][x-1] != 0:
                grid[y][x-1] = 2
    """
    vertical change
    """
    if y > 0 and y < len(grid) - 1:
        if grid[y][x] == 2:
            if grid[y-1][x] != 0:
                grid[y-1][x] = 2
            if grid[y+1][x] != 0:
                grid[y+1][x] = 2
    
    if y == 0:
        if grid[y][x] == 2:
            if grid[y+1][x] != 0:
                grid[y+1][x] = 2
    
    if y == len(grid) - 1:
        if grid[y][x] == 2:
            if grid[y-1][x] != 0:
                grid[y-1][x] = 2
                
x = len(world[0])
y = len(world)

for i in range(y):
    for j in range(x):
        rot_apples(world, j, i)
print()
for row in world:
    print(row)