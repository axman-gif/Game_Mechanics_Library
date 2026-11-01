# -*- coding: utf-8 -*-
"""
Created on Fri Oct 23 21:17:38 2026

@author: AXMAN
GRID_EXPANSION
"""

import random

def create_world(width=20, height=12):
    return [[0 for _ in range(width)] for _ in range(height)]

def print_world(grid):
    for row in grid:
        print(" ".join(f"{val:2}" for val in row))
    print()

def is_border(square, grid, faction):
    x, y = square["x"], square["y"]
    height = len(grid)
    width = len(grid[0])
    directions = {"N":(-1,0),
                  "S":(1,0),
                  "E":(0,1),
                  "W":(0,-1)
                  }
    for dy, dx in directions.values():
        ny, nx = y + dy, x + dx
        if not (0 <= ny < height and 0 <= nx < width):
            return True
        if grid[ny][nx] != faction:
            return True
            
    return False

def is_surrounded(grid, x, y, treat_edges_as_occupied=True):
    height = len(grid)
    width = len(grid[0])
    directions = {"N":(-1,0),
                  "S":(1,0),
                  "E":(0,1),
                  "W":(0,-1)
                  }
    occupied_count = 0
    for dy, dx in directions.values():
        ny, nx = y + dy, x + dx
        if 0 <= ny < height and 0 <= nx < width:
            if grid[ny][nx] != 0:
                occupied_count += 1
        else:
            if treat_edges_as_occupied:
                occupied_count += 1
                
    return occupied_count == 4

def spawn(grid, faction, avoid_edge_traps=True):
    height = len(grid)
    width = len(grid[0])
    valid_positions = []

    for y in range(height):
        for x in range(width):
            if grid[y][x] == 0:
                if not is_surrounded(grid, x, y, treat_edges_as_occupied=avoid_edge_traps):
                    valid_positions.append({"x": x, "y": y})

    if not valid_positions:
        print(f"No hay casillas libres para la facción {faction}.")
        return None

    chosen = random.choice(valid_positions)
    grid[chosen["y"]][chosen["x"]] = faction
    return chosen

class Fort:
    def __init__(self, faction, grid, x=None, y=None):
        self.faction = faction
        self.fort_squares = []
        self.border_squares = []

        # Si se especifican coordenadas x e y válidas, se colocan manualmente
        if x is not None and y is not None:
            grid[y][x] = self.faction
            self.fort_squares.append({"x": x, "y": y})
        # Si se omiten x e y, se delega automáticamente a spawn()
        else:
            spawned = spawn(grid, self.faction)
            if spawned:
                self.fort_squares.append(spawned)

    def expand(self, grid):
        """
        Ejecuta un paso de expansión (1 sola casilla).
        Retorna True si logró expandirse o False si quedó bloqueado sin espacio.
        """
        if not self.fort_squares:
            return False

        height = len(grid)
        width = len(grid[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        candidates = set()
        occupied = {(sq["x"], sq["y"]) for sq in self.fort_squares}

        for sq in self.fort_squares:
            for dy, dx in directions:
                nx, ny = sq["x"] + dx, sq["y"] + dy
                if 0 <= nx < width and 0 <= ny < height:
                    if (nx, ny) not in occupied and grid[ny][nx] == 0:
                        candidates.add((nx, ny))

        if not candidates:
            return False

        chosen_x, chosen_y = random.choice(list(candidates))
        grid[chosen_y][chosen_x] = self.faction
        self.fort_squares.append({"x": chosen_x, "y": chosen_y})
        return True

    def update_borders(self, grid):
        self.border_squares.clear()
        for sq in self.fort_squares:
            if is_border(sq, grid, self.faction):
                self.border_squares.append(sq)
        return self.border_squares

def clear_world(world):
    for y in range(len(world)):
        for x in range(len(world[0])):
            world[y][x] = 0

def restart(world):
    global forts
    forts.clear()
    clear_world(world)
# --- Simulación de partida ---
width = 16
height = 16
world = create_world(width, height)
fort_size = 16

# Instanciación directa en la lista:
# Sin coordenadas (x=None, y=None) -> se posicionan aleatoriamente con spawn()
spawn_points = [[0,0],[width//2,0],[width - 1,0],
                [width//2, height//2],
                [0,height - 1],[width//2,height - 1],[width-1,height-1]]
forts = [Fort(1,world, 8, 8),
         Fort(2,world, 8, 9),
         Fort(3,world, 9, 8),
         Fort(4,world, 7, 8)]
#This comment is to switch to random spawn generation
restart(world)
for n in range(5):
    n += 1
    forts.append(Fort(n, world))
#(Si en algún momento quisieras forzar coordenadas específicas, se escribiría así:)
# forts = [
#     Fort(1, world, x=6, y=10),
#     Fort(2, world, x=7, y=10)
# ]

print("--- Cuadrícula con los puntos de aparición iniciales ---")
print_world(world)

# Expansión simétrica por turnos
for turn in range(fort_size - 1):
    for f in forts:
        f.expand(world)

print("--- Cuadrícula tras expandir los dos fuertes por turnos ---")
print_world(world)

for f in forts:
    f.update_borders(world)
    print(f"Fuerte {f.faction} -> Casillas: {len(f.fort_squares)}, Bordes: {len(f.border_squares)}")