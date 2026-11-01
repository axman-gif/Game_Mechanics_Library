# Interactive Video Game Design Patterns Encyclopedia (`pyray` / Raylib Python)

Welcome! This repository is an **interactive, hands-on laboratory for learning video game design patterns** in Python using **Raylib (`pyray`)**.

Every visual character (2D sprites and 3D articulated models) is built from **pure mathematical primitives** (spheres, cubes, cylinders, rectangular prisms, circles, and lines), and every sound effect and soundtrack is **synthesized in memory** using waveforms—meaning **zero external art or audio files** are required.

---

## Guía Rápida para Principiantes (Español)

Si acabas de descargar este repositorio desde GitHub y estás dando tus primeros pasos en Python o en el desarrollo de videojuegos, sigue estos 4 pasos:

### 1. Requisitos previos
* Tener instalado **Python 3.10 o superior** ([descargar de python.org](https://www.python.org/downloads/)).
  * *Nota en Windows:* Al instalar Python, asegúrate de marcar la casilla **"Add python.exe to PATH"**.

### 2. Instalación (en menos de 1 minuto)
Abre una terminal (`PowerShell`, `CMD` o `Terminal` en Linux/macOS) dentro de la carpeta del proyecto y ejecuta:

```bash
# 1. (Opcional pero recomendado) Crear un entorno virtual
python -m venv .venv

# 2. Activar el entorno virtual:
# En Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# En Windows (CMD):
.venv\Scripts\activate.bat
# En Linux / macOS:
source .venv/bin/activate

# 3. Instalar la única dependencia (Raylib para Python)
pip install -r requirements.txt
```

### 3. Cómo ejecutar el Lanzador Interactivo (`launcher.py`)
Para explorar todos los prototipos, leer qué patrón de diseño enseña cada uno y lanzarlos con un clic o `Enter`:

```bash
python -B launcher.py
```

También puedes ejecutar cualquier minijuego directamente desde la carpeta `minigames/`:

```bash
python -B minigames/space_swarm.py
```

### 4. Controles Globales de Interfaz y Aprendizaje (En el Launcher y en todos los Minijuegos)
Tanto en `launcher.py` como dentro de cualquier minijuego dispones de una **barra superior de configuración** cuyos ajustes se guardan automáticamente en `config.json`:

* **Menú desplegable `Font` (Tipo de letra):** Cambia en vivo entre la fuente clásica pixelada de Raylib (`Default (Pixel)`) y las fuentes TrueType detectadas en tu sistema (`Consolas`, `Segoe UI`, `Courier New`, `Arial`, `Verdana`, etc.).
* **Menú desplegable `Size` y atajos `Ctrl + "+"` / `Ctrl + "-"`:** Aumenta o disminuye el tamaño de letra de toda la interfaz en tiempo real.
* **Menú desplegable `Win` y tecla `F11`:** Cambia el tamaño de la ventana (`1024x576`, `1280x720`, `1600x900`, `1920x1080`) o presiona **`F11`** en cualquier momento para alternar **Pantalla Completa (Fullscreen)**.
* **Tecla `[Tab]` (Modo Rayos X / Telemetría):** Muestra u oculta en tiempo real las tripas matemáticas del patrón (celdas activas del *Spatial Grid*, uso de memoria del *Object Pool*, estados de IA, etc.).
* **Tecla `[F1]` (Interruptor del Patrón):** Activa o desactiva el patrón en vivo para que sientas la diferencia entre jugar *con* el patrón y *sin* él.

### 5. Filosofía del Código: Transferibilidad directa a C++ y otros lenguajes
En este proyecto **Python se utiliza únicamente como "pseudocódigo ejecutable"** por su simplicidad y rápida lectura. Todo el código sigue reglas estrictas en [`AGENTS.md`](AGENTS.md) para **evitar características exclusivas de Python** (prohibido usar decoradores `@dataclass` / `@property`, generadores `yield`, métodos mágicos `__dunder__`, `lambda` o comprensiones de listas complejas).

De esta manera, si estás aprendiendo para programar tus propios videojuegos en **C++, C, C#, Rust o Zig**, puedes traducir cada estructura de datos y algoritmo línea por línea sin quebrarte la cabeza:

| Concepto en este repositorio (Python + `pyray`) | Equivalente directo en C++ (`raylib.h`) |
| :--- | :--- |
| `class Bullet:` con atributos explícitos en `__init__` | `struct Bullet { Vector2 pos; Vector2 vel; bool active; };` |
| Arreglo preasignado (`self.pool` con bandera `b.active`) | `std::array<Bullet, 600> pool;` o `std::vector<Bullet>` |
| Bucles explícitos `for i in range(count):` con `if/else` | `for (int i = 0; i < count; ++i) { ... }` |
| `init_window(1280, 720, "Title")` / `begin_drawing()` | `InitWindow(1280, 720, "Title");` / `BeginDrawing();` |
| `draw_rectangle(x, y, w, h, color)` / `draw_sphere(...)` | `DrawRectangle(x, y, w, h, color);` / `DrawSphere(...);` |

---

## Beginner Quick-Start Guide (English)

### 1. Prerequisites & Setup
Make sure you have **Python 3.10+** installed, then open a terminal in the project root directory and run:

```bash
# Install Raylib CFFI bindings (`pyray`)
pip install -r requirements.txt
```

### 2. Launching the Interactive Pattern Hub
Run the graphical launcher to browse all prototypes, inspect their pattern documentation, run automated smoke tests, and play:

```bash
python -B launcher.py
```

Or run any standalone prototype directly:

```bash
python -B minigames/space_swarm.py
```

### 3. Global UI Bar & Shortcuts (`config.json`)
Every window in this repository (`launcher.py` and all scripts in `minigames/`) features a persistent top settings bar backed by `config.json`:

| Control / Widget | Action |
| :--- | :--- |
| **`Font` Dropdown** | Switch live between `Default (Pixel)` and system TrueType fonts (`Consolas`, `Segoe UI`, `Arial`, etc.). |
| **`Size` Dropdown / `Ctrl + '+'` & `Ctrl + '-'`** | Increase or decrease UI font size across all panels and HUDs. |
| **`Win` Dropdown / `[F11]`** | Switch window resolution (`1024x576` to `1920x1080`) or toggle **Fullscreen (`F11`)**. |
| **`[Tab]`** | Toggle the **X-Ray Pattern Telemetry & Debug Overlay** to inspect the pattern in real time. |
| **`[F1]`** | Toggle the target design pattern `ON / OFF` to feel what happens without it. |

### 4. Cross-Language & C++ Transferability Philosophy
Python is used here strictly for **clarity and zero-compile-time iteration**, not for Python-specific syntactic tricks. Every script adheres to the **Language-Agnostic Code Rules** in [`AGENTS.md`](AGENTS.md):
* **No Python-exclusive magic**: No decorators (`@dataclass`, `@property`), no generators (`yield`), no dunder operator overloading, and no nested list comprehensions.
* **1-to-1 C++ Mapping**: All entities, pools, spatial grids, and state machines are built with plain `struct`-like classes, fixed-capacity arrays, integer indices, and explicit `for` loops so you can port any pattern directly to **C++, C, C#, Rust, or Zig**.

---

## Repository Structure

```text
./
├── README.md                  # Beginner guide & setup instructions
├── AGENTS.md                  # AI Agent operating instructions & pedagogical template
├── config.json                # Saved user preferences (font, font size, window size)
├── launcher.py                # Interactive Pattern Encyclopedia & Minigame Hub
├── requirements.txt           # Python dependencies (`raylib`)
├── patrones.md                # Comprehensive catalog of 2D & 3D game design patterns
├── minigames.md               # Registry of built & planned single-pattern prototypes
├── assets.md                  # Documentation for procedural 3D models, 2D sprites & audio
├── utils.md                   # Documentation for collisions, spatial grids, AI, math & UI
├── assets/                    # Procedural 3D/2D primitives and in-memory audio synth
├── utils/                     # Non-native collisions, SpatialGrid2D/3D, AI steering & UI manager
└── minigames/                 # Standalone, single-file minigames and pattern labs
    └── space_swarm.py         # 2D Bullet Hell showcasing Object Pool, SpatialGrid2D & TraumaShake
```

