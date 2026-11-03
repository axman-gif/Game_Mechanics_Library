# 🎮 Video Game Design Patterns Library (`pyray` / Raylib Python)

<div align="center">

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Raylib](https://img.shields.io/badge/Raylib-pyray%206.0%2B-D73A49?style=for-the-badge&logo=raylib&logoColor=white)](https://www.raylib.com/)
[![Assets](https://img.shields.io/badge/Art%20Assets-0%20(100%25%20Procedural)-2ea44f?style=for-the-badge)](assets.md)
[![Audio](https://img.shields.io/badge/Audio-Synthesized%20in%20RAM-orange?style=for-the-badge)](assets.md)
[![Gamepad](https://img.shields.io/badge/Input-Dual%20KB%2FM%20%2B%20Gamepad-8A2BE2?style=for-the-badge)](utils.md)
[![C++ Ready](https://img.shields.io/badge/Code%20Style-1%3A1%20C%2B%2B%20Transferable-blue?style=for-the-badge)](AGENTS.md)

**An interactive, beginner-friendly encyclopedia of video game programming patterns.**  
*Learn game architecture hands-on with pure geometric math, in-memory sound synthesis, live telemetry, and zero black-box game engines.*

---

### 🌐 Select Language / Selecciona tu Idioma
[🇬🇧 **English Guide**](#-english-guide) &nbsp;|&nbsp; [🇪🇸 **Guía en Español**](#-guía-en-español)

---

</div>

## 📑 Table of Contents / Tabla de Contenido
- [🇬🇧 English Guide](#-english-guide)
  - [🌟 What is this Project?](#-what-is-this-project)
  - [✨ Interactive Learning Features](#-interactive-learning-features)
  - [🚀 Quick-Start for Beginners (Step-by-Step)](#-quick-start-for-beginners-step-by-step)
  - [🕹️ How to Play & Explore](#️-how-to-play--explore)
  - [🎮 Global Controls (Keyboard, Mouse & Gamepad)](#-global-controls-keyboard-mouse--gamepad)
  - [🧩 Built Minigames & Pattern Showcase](#-built-minigames--pattern-showcase)
  - [💡 The "No-Magic" C++ Porting Philosophy](#-the-no-magic-c-porting-philosophy)
- [🇪🇸 Guía en Español](#-guía-en-español)
  - [🌟 ¿Qué es este proyecto?](#-qué-es-este-proyecto)
  - [✨ Características Interactivas de Aprendizaje](#-características-interactivas-de-aprendizaje)
  - [🚀 Guía Rápida para Principiantes (Paso a Paso)](#-guía-rápida-para-principiantes-paso-a-paso)
  - [🕹️ Cómo Jugar y Explorar](#️-cómo-jugar-y-explorar)
  - [🎮 Controles Globales (Teclado, Ratón y Mando)](#-controles-globales-teclado-ratón-y-mando)
  - [🧩 Catálogo de Minijuegos y Patrones](#-catálogo-de-minijuegos-y-patrones)
  - [💡 Filosofía "Cero Magia": Transferibilidad a C++](#-filosofía-cero-magia-transferibilidad-a-c)
- [📁 Repository Map / Estructura del Proyecto](#-repository-map--estructura-del-proyecto)
- [❓ Frequently Asked Questions & Troubleshooting](#-frequently-asked-questions--troubleshooting)

---

# 🇬🇧 English Guide

## 🌟 What is this Project?

Learning video game architecture is often frustrating for beginners. Modern engines like Unity, Unreal, or Godot hide the underlying math behind complex editors and gigabytes of dependencies, while traditional programming tutorials often get bogged down downloading 3D models, textures, and audio files.

This repository takes a radically different, ultra-clear approach:
1. **Zero External Art & Audio Assets**: Every 2D sprite and 3D character is built in real time using **mathematical primitives** (spheres, cubes, cylinders, lines, polygons). Every sound effect and background chord is **procedurally synthesized in RAM** using raw waveforms (sine, square, saw).
2. **Single-File Laboratories**: Every minigame inside `minigames/` is completely standalone. You can open a single `.py` file, read how the pattern works, change numbers, and immediately see the results.
3. **Pure, C++-Transferable Logic**: We use Python strictly as **executable pseudocode**. No confusing "Python magic" (no decorators, no generators, no complex comprehensions). Everything is written with simple structs, explicit arrays, and loops that translate **1-to-1 to C++, C, C#, Rust, or Zig**.
4. **Dual Controls Out-of-the-Box**: Plug in any modern controller (Xbox, PlayStation, or generic USB gamepad) and it will work seamlessly alongside your Keyboard and Mouse simultaneously.

---

## ✨ Interactive Learning Features

Every minigame in this collection includes two signature pedagogical tools:

> [!TIP]
> ### 🔬 1. The X-Ray Inspector (`[Tab]` or Gamepad `Y` / `Select`)
> Press **`[Tab]`** at any time to peel back the graphics and view the mathematical machinery underneath:
> - **Spatial Hash Grids**: Watch cell boundaries highlight as entities move across them.
> - **Object Pools**: Inspect active vs. available bullet slots and allocation metrics live.
> - **AI Brains**: See Behavior Tree and Finite State Machine (FSM) states change in real time.
> - **Physics & Rays**: Visualize collision capsules, line-of-sight raycasts, and trajectory vectors.

> [!NOTE]
> ### 🎚️ 2. The Live Pattern Toggle (`[F1]` or Gamepad `LB` / `L1`)
> Want to understand *why* a design pattern matters? Press **`[F1]`** to turn the pattern **OFF** during gameplay:
> - Turn off the **Object Pool** and feel the frame-rate hitch as memory gets allocated dynamically.
> - Turn off the **Spatial Grid** and watch CPU usage spike as collision checks degrade to $O(N^2)$.
> - Turn off **Camera Trauma Damping** and experience how stiff and jarring unsmoothed screens feel.
> - Press **`[F1]`** again to turn the pattern back **ON** and instantly feel the difference!

---

## 🚀 Quick-Start for Beginners (Step-by-Step)

You do **not** need to be an expert programmer or have Visual Studio installed to run this project. You only need standard Python!

### Step 1: Install Python 3.10+
1. Go to the official website: [python.org/downloads](https://www.python.org/downloads/).
2. Download and run the installer for your operating system.
3. > [!IMPORTANT]
   > **Windows Users**: On the very first screen of the installer, **check the box that says "Add python.exe to PATH"** before clicking Install. This enables you to run Python from any command line.

### Step 2: Download or Clone this Repository
- **With Git**:
  ```bash
  git clone https://github.com/AXMAN/Game_Mechanics_Library.git
  cd Game_Mechanics_Library
  ```
- **Without Git**: Click the green **Code** button at the top of this GitHub page, select **Download ZIP**, and extract it into a folder on your computer.

### Step 3: Create & Activate a Virtual Environment
A virtual environment ensures the project's dependencies don't interfere with the rest of your system. Open your terminal inside the project folder:

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell shows a script execution error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and try activating again).*

**On Windows (Command Prompt - CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 4: Install Raylib (Only 1 Dependency!)
This project only requires the official Raylib CFFI package (`pyray`):
```bash
pip install -r requirements.txt
```

---

## 🕹️ How to Play & Explore

### Option A: The Interactive Visual Hub (`launcher.py`)
The easiest way to explore the encyclopedia is with our built-in graphical launcher:
```bash
python -B launcher.py
```
*(The `-B` flag prevents Python from creating unnecessary `__pycache__` folders).*

Within the launcher:
- Browse minigames grouped by category (**Menus & UI**, **Combat & Weapons**, **Enemies & AI**, etc.).
- Read the **Problem Solved** and **How the Pattern Works** right inside the UI.
- Press **`Enter`** or click **`Launch Prototype`** to play.
- Press **`T`** or click **`Run Smoke Test`** to run an automated 3-frame integrity check.

### Option B: Run Any Minigame Directly
Every minigame is completely standalone. You can run any script straight from your terminal:
```bash
python -B minigames/<category_subfolder>/<script_name>.py

# Example:
# python -B minigames/3.0_core_prototypes/orbital_siege.py
```

---

## 🎮 Global Controls (Keyboard, Mouse & Gamepad)

All prototypes feature unified controls with simultaneous Keyboard/Mouse and Gamepad support:

| Action | Keyboard & Mouse | Gamepad / Controller |
| :--- | :--- | :--- |
| **Movement / Navigate** | `W` `A` `S` `D` / Arrow Keys | **Left Analog Stick** (with radial deadzone) or **D-Pad** |
| **Aim / Reticle / Look** | **Mouse Cursor** / `Q` & `E` | **Right Analog Stick** (steers reticle or 3D camera) |
| **Primary Action / Select** | `Space` / Left Mouse Button / `Enter` | **Face Button A** (Xbox) / **Cross** (PlayStation) / `RT` |
| **Secondary Action / Back** | `Right Click` / `Esc` / `Backspace` | **Face Button B** (Xbox) / **Circle** (PlayStation) / `LT` |
| **🔬 X-Ray Debug Overlay** | **`[Tab]`** | **Face Button Y** (Xbox) / **Triangle** / **View (Select)** |
| **🎚️ Live Pattern Toggle** | **`[F1]`** | **Left Bumper (`LB` / `L1`)** or **R3** |
| **🔄 Reset Simulation** | **`[R]`** | **Start (Menu)** |
| **🔤 Font Size Adjust** | **`Ctrl + '+'`** / **`Ctrl + '-'`** | *Use Top Bar Dropdown* |
| **🖥️ Toggle Fullscreen** | **`[F11]`** | *Use Top Bar Dropdown* |

> [!TIP]
> ### ⚙️ The Global Top Settings Bar
> Every window displays an interactive bar at the top:
> - **`Font`**: Switch live between Raylib's pixel font and your system's TrueType fonts (`Consolas`, `Segoe UI`, `Arial`, etc.).
> - **`Size`**: Adjust UI text size on the fly.
> - **`Win`**: Change window resolution (`1024x576`, `1280x720`, `1600x900`, `1920x1080`) or toggle Fullscreen (`F11`).
> - **`PAD Status`**: Live indicator showing whether your controller is detected (`PAD: ON` vs `PAD: OFF`).
> 
> *All your settings are automatically saved in `config.json`.*

---

## 🧩 Built Minigames & Pattern Showcase

The library organizes minigames and experimental laboratories into designated subfolders under [`minigames/`](minigames/):

| Section | Category Subfolder | Dimension & Scope | Description of Laboratory Mechanics |
| :---: | :--- | :---: | :--- |
| **3.0** | [`3.0_core_prototypes/`](minigames/3.0_core_prototypes/) | **2D / 3D Full Slices** | Multi-pattern arcade and strategy loops combining 4+ systems (orbital gravity wells, procedural IK behemoths, subterranean excavation drills, 6-DOF space dogfights, turn-based tactics, and RTS outposts). |
| **3.1** | [`3.1_menus_ui/`](minigames/3.1_menus_ui/) | **2D / 3D Menus & UI** | Tactile and responsive interface architectures: diegetic 3D displays, polyomino inventories, modular weapon socket DAGs, radial wheels, maximalist 4X ledgers, and unified cross-platform touch/mouse viewports. |
| **3.2** | [`3.2_combat_weapons/`](minigames/3.2_combat_weapons/) | **2D / 3D Combat** | Kinetic weapon ballistics, parabolic mortars, penetrating hitscan, recoil bloom springs, active reload timing, fighting game frame-data arcs, parry stagger windows, elemental reactions, and RTS siege splash. |
| **3.3** | [`3.3_enemies_ai/`](minigames/3.3_enemies_ai/) | **2D / 3D AI Systems** | Autonomous enemy steering, flocking boids, Dijkstra flow fields for swarms, tactical cover scoring, visualized behavior trees, threat aggro tables, multi-phase bosses, and RTS military formation steering. |
| **3.4** | [`3.4_progression_economy/`](minigames/3.4_progression_economy/) | **2D Progression** | Mathematical progression and economy models: CDF loot drop histograms, polynomial/exponential XP curves, crafting DAGs, market supply/demand, deckbuilder cycles, and 4X resource flow ledgers. |
| **3.5** | [`3.5_world_exploration/`](minigames/3.5_world_exploration/) | **2D / 3D Worlds** | Procedural generation and exploration: cellular automata caverns, BSP dungeons, Amanatides-Woo DDA voxel raymarching, infinite chunk streaming, dynamic day-night orbits, and dual-layer fog of war. |
| **3.6** | [`3.6_movement_camera/`](minigames/3.6_movement_camera/) | **2D / 3D Movement** | Movement kinematics and game feel: Coyote time and jump buffers, Verlet pendulum grapples, 3D Quake-style strafing controllers, spring-arm orbit cameras, trauma screen shake, and RTS panning cameras. |
| **3.7** | [`3.7_puzzle_stealth/`](minigames/3.7_puzzle_stealth/) | **2D / 3D Systems** | Discrete logic and systemic interactions: Sokoban deadlock detection with undo/redo stacks, stealth illumination sensors, cellular fluid automata, lockpicking sweet spots, and RTS marquee box selection. |

---

## 💡 The "No-Magic" C++ Porting Philosophy

In this repository, Python is used exclusively for its accessibility and instant iteration. We strictly avoid Python-only idioms so you can easily translate any pattern into **C++, C, C#, Rust, or Zig**:

```
❌ Forbidden in our code:            ✅ Used instead:
---------------------------------------------------------------------------------
No @dataclass or @property           Explicit struct-like classes with __init__
No generators (yield) or async       Explicit frame-by-frame update(dt) functions
No magic dunders (__call__, etc.)    Named methods (pool.get_slot(), add_vectors())
No per-frame list comprehensions     Pre-allocated fixed arrays & in-place loops
No dynamic getattr/eval/metaclasses  Direct field access and explicit integers
```

### Direct 1-to-1 Mapping to C++:

| Pattern Concept in this Repo (Python + `pyray`) | Equivalent Direct C++ Code (`raylib.h`) |
| :--- | :--- |
| `class Bullet:` with fields set in `__init__` | `struct Bullet { Vector2 pos; Vector2 vel; bool active; };` |
| `self.pool = [Bullet() for _ in range(600)]` | `std::array<Bullet, 600> pool;` |
| `for i in range(len(self.pool)):` with `if/else` | `for (int i = 0; i < pool.size(); ++i) { ... }` |
| `init_window(1280, 720, "Title")` | `InitWindow(1280, 720, "Title");` |
| `draw_sphere(pos, radius, color)` | `DrawSphere(pos, radius, color);` |

---
---

# 🇪🇸 Guía en Español

## 🌟 ¿Qué es este proyecto?

Aprender la arquitectura interna de los videojuegos suele ser abrumador para quienes dan sus primeros pasos. Los motores comerciales como Unity, Unreal o Godot esconden la matemática y la lógica detrás de interfaces pesadas y descargas gigantescas, mientras que los tutoriales tradicionales suelen perder horas descargando modelos 3D, texturas y archivos de audio.

Este repositorio propone un método radicalmente distinto, claro y educativo:
1. **Cero Recursos Externos (Gráficos y Audio 100% Procedurales)**: Cada sprite 2D y modelo 3D articulado se construye en tiempo real mediante **primitivas geométricas** (esferas, cubos, cilindros, líneas y polígonos). Cada efecto de sonido y acorde musical se **sintetiza en memoria RAM** a partir de ondas matemáticas (senoidal, cuadrada, sierra). ¡No necesitas descargar ningún archivo de arte o audio!
2. **Laboratorios en un Solo Archivo**: Cada minijuego dentro de `minigames/` es 100% autónomo. Puedes abrir un archivo `.py`, leer cómo funciona el patrón, cambiar números y ver el resultado de inmediato.
3. **Lógica Pura y Traducible 1:1 a C++**: Utilizamos Python únicamente como **pseudocódigo ejecutable**. No hay "magia oculta" de Python (nada de decoradores extraños, generadores o comprensiones crípticas). Todo está escrito con estructuras simples, arreglos fijos e índices numéricos que puedes portar directamente a **C++, C, C#, Rust o Zig**.
4. **Soporte de Mando/Gamepad de Fábrica**: Conecta cualquier mando de videojuegos (Xbox, PlayStation o genérico USB) y funcionará automáticamente junto al teclado y ratón de forma simultánea.

---

## ✨ Características Interactivas de Aprendizaje

Cada prototipo incluye dos herramientas pedagógicas fundamentales:

> [!TIP]
> ### 🔬 1. El Inspector de Rayos X (`[Tab]` o Mando `Y` / `Select`)
> Presiona **`[Tab]`** en cualquier momento para hacer transparentes los gráficos y ver la maquinaria matemática en tiempo real:
> - **Rejillas Espaciales (*Spatial Grid*)**: Observa cómo se iluminan las celdas de colisión al moverse los objetos.
> - **Reserva de Objetos (*Object Pool*)**: Inspecciona cuántos proyectiles están activos vs disponibles sin saturar la memoria.
> - **Cerebros de IA**: Observa los nodos activos de los Árboles de Comportamiento (*Behavior Trees*) y Máquinas de Estados (*FSM*).
> - **Vectores y Físicas**: Visualiza cápsulas de colisión 3D, líneas de visión (*Raycasts*) y vectores de aceleración.

> [!NOTE]
> ### 🎚️ 2. El Interruptor del Patrón (`[F1]` o Mando `LB` / `L1`)
> ¿Quieres entender *por qué* existe un patrón de diseño? Presiona **`[F1]`** para **DESACTIVARLO** en pleno juego:
> - Apaga el **Object Pool** y siente los tirones en los fotogramas cuando la memoria se asigna y destruye en bucle.
> - Apaga la **Rejilla Espacial** y observa cómo el procesador se satura al comparar colisiones de todos contra todos ($O(N^2)$).
> - Apaga la **Suavización de Cámara** y siente lo tosca que se vuelve la experiencia sin amortiguamiento matemático.
> - ¡Vuelve a pulsar **`[F1]`** para reactivar el patrón y comprobar la enorme mejora!

---

## 🚀 Guía Rápida para Principiantes (Paso a Paso)

¡No necesitas ser un experto ni tener compiladores complejos instalados! Solo requieres Python estándar:

### Paso 1: Instalar Python 3.10 o superior
1. Ingresa a la página oficial: [python.org/downloads](https://www.python.org/downloads/).
2. Descarga y ejecuta el instalador correspondiente a tu sistema operativo.
3. > [!IMPORTANT]
   > **En Windows**: En la primera pantalla del instalador, **marca obligatoriamente la casilla "Add python.exe to PATH"** antes de presionar Instalar. Esto te permitirá ejecutar comandos desde la terminal.

### Paso 2: Descargar o Clonar el Repositorio
- **Con Git**:
  ```bash
  git clone https://github.com/AXMAN/Game_Mechanics_Library.git
  cd Game_Mechanics_Library
  ```
- **Sin Git**: Haz clic en el botón verde **Code** arriba a la derecha en esta página de GitHub, selecciona **Download ZIP**, y descomprímelo en una carpeta de tu preferencia.

### Paso 3: Crear y Activar un Entorno Virtual
Un entorno virtual evita conflictos con otras versiones o librerías de tu equipo. Abre una terminal dentro de la carpeta del proyecto y ejecuta:

**En Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
*(Si PowerShell muestra un aviso de directiva de ejecución, escribe `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` y vuelve a activar).*

**En Windows (Símbolo del Sistema - CMD):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**En macOS o Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 4: Instalar Raylib (¡Única dependencia!)
Solo necesitamos la librería gráfica oficial de Raylib para Python (`pyray`):
```bash
pip install -r requirements.txt
```

---

## 🕹️ Cómo Jugar y Explorar

### Opción A: El Lanzador Visual Interactivo (`launcher.py`)
Es la manera más cómoda y recomendada de recorrer toda la enciclopedia:
```bash
python -B launcher.py
```
*(El modificador `-B` evita que Python genere carpetas temporales `__pycache__`).*

Dentro del lanzador podrás:
- Filtrar los minijuegos por categoría (**Menús e Interfaz**, **Combate**, **IA y Enemigos**, etc.).
- Leer el **Problema Resuelto** y la **Explicación Matemática** de cada patrón antes de jugar.
- Pulsar **`Enter`** o hacer clic en **`Launch Prototype`** para abrir el minijuego.
- Pulsar **`T`** o hacer clic en **`Run Smoke Test`** para realizar una prueba automática de 3 fotogramas.

### Opción B: Ejecutar Cualquier Minijuego Directamente
Cada minijuego es un archivo independiente. Puedes ejecutar el que desees directamente desde la terminal:
```bash
python -B minigames/<subcarpeta_de_categoria>/<nombre_del_script>.py

# Ejemplo:
# python -B minigames/3.0_core_prototypes/orbital_siege.py
```

---

## 🎮 Controles Globales (Teclado, Ratón y Mando)

Todos los minijuegos responden a un esquema unificado de controles que combina teclado, ratón y gamepad al mismo tiempo:

| Acción | Teclado y Ratón | Mando / Gamepad |
| :--- | :--- | :--- |
| **Moverse / Navegar** | `W` `A` `S` `D` / Flechas del teclado | **Stick Analógico Izquierdo** (con zona muerta radial) o **D-Pad** |
| **Apuntar / Mirilla / Vista** | **Cursor del Ratón** / `Q` y `E` | **Stick Analógico Derecho** (apunta la mirilla o gira la cámara 3D) |
| **Acción Principal / Seleccionar** | `Espacio` / Clic Izquierdo / `Enter` | **Botón A** (Xbox) / **Cruz** (PlayStation) / Gatillo `RT` |
| **Acción Secundaria / Cancelar** | `Clic Derecho` / `Esc` / `Backspace` | **Botón B** (Xbox) / **Círculo** (PlayStation) / Gatillo `LT` |
| **🔬 Modo Rayos X (Telemetría)** | **`[Tab]`** | **Botón Y** (Xbox) / **Triángulo** / **Botón View (Select)** |
| **🎚️ Activar/Desactivar Patrón** | **`[F1]`** | **Botón Superior Izquierdo (`LB` / `L1`)** o **R3** |
| **🔄 Reiniciar Simulación** | **`[R]`** | **Botón Start (Menú)** |
| **🔤 Ajustar Tamaño de Letra** | **`Ctrl + '+'`** / **`Ctrl + '-'`** | *Usa el menú desplegable superior* |
| **🖥️ Alternar Pantalla Completa** | **`[F11]`** | *Usa el menú desplegable superior* |

> [!TIP]
> ### ⚙️ La Barra Superior de Ajustes Globales
> Todas las ventanas del proyecto cuentan con una barra superior interactiva:
> - **`Font`**: Alterna en vivo entre la fuente pixelada clásica de Raylib y las fuentes TrueType de tu sistema (`Consolas`, `Segoe UI`, `Arial`, etc.).
> - **`Size`**: Ajusta el tamaño de la letra de toda la interfaz en vivo.
> - **`Win`**: Cambia la resolución (`1024x576`, `1280x720`, `1600x900`, `1920x1080`) o activa **Pantalla Completa (`F11`)**.
> - **`PAD Status`**: Indicador visual que te muestra en tiempo real si tu mando está conectado (`PAD: ON` vs `PAD: OFF`).
> 
> *Tus preferencias se guardan automáticamente en `config.json` para tus próximas partidas.*

---

## 🧩 Catálogo de Minijuegos y Patrones

El proyecto organiza sus minijuegos y laboratorios experimentales en subcarpetas temáticas dentro de [`minigames/`](minigames/):

| Sección | Subcarpeta de la Categoría | Dimensión y Alcance | Descripción del Contenido y Mecánicas |
| :---: | :--- | :---: | :--- |
| **3.0** | [`3.0_core_prototypes/`](minigames/3.0_core_prototypes/) | **2D / 3D Rebanadas Completas** | Bucles arcade y de estrategia multi-patrón que combinan 4+ sistemas (gravedad orbital, colosos con IK procedimental, taladros de excavación, combate espacial 6-DOF, táctica por turnos y estrategia RTS). |
| **3.1** | [`3.1_menus_ui/`](minigames/3.1_menus_ui/) | **2D / 3D Menús e Interfaces** | Arquitecturas de interfaz táctil y responsiva: pantallas diegéticas 3D, inventarios por poliominós, bancos de modificación modular con grafos DAG, ruedas radiales, libros de cuentas 4X maximalistas y navegación unificada ratón/táctil. |
| **3.2** | [`3.2_combat_weapons/`](minigames/3.2_combat_weapons/) | **2D / 3D Sistemas de Combate** | Balística de proyectiles cinéticos, morteros parabólicos, hitscan con penetración, resortes de retroceso y dispersión, recargas activas, arcos de daño por fotogramas (*frame data*), ventanas de parry y daño de área RTS. |
| **3.3** | [`3.3_enemies_ai/`](minigames/3.3_enemies_ai/) | **2D / 3D IA y Comportamientos** | Dirección autónoma de enemigos, bandadas *boids*, campos de flujo Dijkstra para hordas, árboles de comportamiento visualizados, tablas de amenaza *aggro*, jefes por fases y formaciones militares RTS. |
| **3.4** | [`3.4_progression_economy/`](minigames/3.4_progression_economy/) | **2D Economía y Progresión** | Modelos matemáticos de progresión: tablas de botín con muestreo CDF, curvas de nivel polinomiales/exponenciales, redes de crafteo DAG, simulador de *pity* gacha y flujos macroeconómicos 4X. |
| **3.5** | [`3.5_world_exploration/`](minigames/3.5_world_exploration/) | **2D / 3D Mundos y Entorno** | Generación procedimental y exploración: cavernas por autómatas celulares, mazmorras BSP, vóxeles 3D con DDA de Amanatides-Woo, niebla de guerra de doble capa y generación de biomas hexagonales. |
| **3.6** | [`3.6_movement_camera/`](minigames/3.6_movement_camera/) | **2D / 3D Físicas y Cámaras** | Sensación cinemática (*game feel*): Coyote time y almacenamiento de saltos (*jump buffer*), péndulos Verlet para garfios, controladores 3D tipo Quake, cámaras con resorte anti-oclusión y cámaras RTS. |
| **3.7** | [`3.7_puzzle_stealth/`](minigames/3.7_puzzle_stealth/) | **2D / 3D Lógica y Sigilo** | Lógica discreta e interacciones sistémicas: puzles Sokoban con detección de bloqueos y pila Deshacer/Rehacer, sensores de iluminación de sigilo, fluidos celulares, ganzúas y cajas de selección (*marquee*). |

---

## 💡 Filosofía "Cero Magia": Transferibilidad a C++

En este proyecto, Python se emplea exclusivamente por su velocidad de lectura y agilidad para iterar. Prohibimos expresamente cualquier truco exclusivo de Python para que puedas tomar cualquiera de estos algoritmos y portarlo línea por línea a **C++, C, C#, Rust o Zig**:

```
❌ Prohibido en este repositorio:          ✅ Utilizado en su lugar:
---------------------------------------------------------------------------------
Nada de @dataclass ni @property            Clases planas estilo struct con __init__
Nada de generadores (yield) ni async       Funciones de avance por fotograma update(dt)
Nada de métodos mágicos (__call__, etc.)   Métodos con nombre explícito (pool.get(), etc.)
Nada de comprensiones de lista por frame   Arreglos preasignados y bucles explícitos
Nada de metaprogramación dinámica          Acceso directo a variables y enteros
```

### Tabla de Traducción Directa a C++:

| Concepto en Python (`pyray`) | Código equivalente directo en C++ (`raylib.h`) |
| :--- | :--- |
| `class Bullet:` con variables en `__init__` | `struct Bullet { Vector2 pos; Vector2 vel; bool active; };` |
| `self.pool = [Bullet() for _ in range(600)]` | `std::array<Bullet, 600> pool;` |
| Bucles `for i in range(len(self.pool)):` con `if/else` | `for (int i = 0; i < pool.size(); ++i) { ... }` |
| `init_window(1280, 720, "Título")` | `InitWindow(1280, 720, "Título");` |
| `draw_sphere(pos, radio, color)` | `DrawSphere(pos, radio, color);` |

---
---

# 📁 Repository Map / Estructura del Proyecto

```text
Game_Mechanics_Library/
├── README.md                  # 📖 Este manual / Beginner's manual (English & Español)
├── AGENTS.md                  # 🤖 Reglas de arquitectura y plantilla pedagógica en 5 bloques
├── config.json                # ⚙️ Preferencias persistentes de interfaz (fuente, tamaño, ventana)
├── launcher.py                # 🚀 Lanzador visual interactivo y catálogo general
├── requirements.txt           # 📦 Única dependencia del proyecto: raylib (pyray)
├── patterns.md                # 📚 Enciclopedia teórica de patrones de diseño de videojuegos
├── minigames.md               # 📋 Registro detallado de todos los minijuegos construidos y planificados
├── assets.md                  # 🎨 Documentación de modelos 3D y sprites 2D procedurales y audio
├── utils.md                   # 🧮 Documentación de colisiones no-nativas, rejillas y matemáticas
│
├── assets/                    # 🎨 Biblioteca de recursos matemáticos (¡Cero archivos externos!)
│   ├── models_3d/             #    Modelos 3D por primitivas (humanoide, cuadrúpedo, dron, torreta)
│   ├── sprites_2d/            #    Sprites 2D por primitivas geométricas animadas
│   └── audio/                 #    Sintetizador en memoria RAM de efectos de sonido (SFX) y música (BGM)
│
├── utils/                     # 🧮 Utilidades matemáticas y de entrada
│   ├── collisions.py          #    Cápsula rotada 3D/2D, SAT OBB y proyecciones de segmentos
│   ├── spatial_grid.py        #    Rejillas espaciales 2D y 3D (SpatialGrid2D / SpatialGrid3D)
│   ├── ai_pursuit.py          #    Algoritmos de dirección (Seek, Intercept), A* y línea de visión (LOS)
│   ├── math_helpers.py        #    Lerp, amortiguamiento (damp), curvas y temblor de cámara (TraumaShake)
│   ├── ui_settings.py         #    Barra superior con dropdowns de fuentes, tamaños (Ctrl +/-) y F11
│   └── gamepad_input.py       #    Mapeo simultáneo de Teclado/Ratón y Mando con zona muerta radial
│
└── minigames/                 # 🎮 Prototipos y laboratorios de aprendizaje clasificados
    ├── 3.0_core_prototypes/   #    Prototipos completos multi-patrón (Space Swarm, Mecha Colosseum, Drone Defense)
    │   ├── drone_defense_3d.py
    │   ├── mecha_colosseum.py
    │   └── space_swarm.py
    ├── 3.1_menus_ui/          #    Laboratorios de interfaz, menús e inventarios táctiles
    │   ├── attache_case.py
    │   ├── gear_compare.py
    │   ├── merchant_stall.py
    │   ├── minimap_compass.py
    │   ├── overloaded_mule.py
    │   ├── paper_doll.py
    │   ├── skill_web.py
    │   ├── tabbed_status_menu.py
    │   ├── tetris_backpack.py
    │   ├── title_screen_cursor.py
    │   ├── weapon_wheel.py
    │   └── workbench.py
    ├── 3.2_combat_weapons/    #    Sistemas de combate, balística y armas (en desarrollo)
    ├── 3.3_enemies_ai/        #    Comportamientos de enemigos e IA (en desarrollo)
    ├── 3.4_progression_economy/#   Economía, crafteo y progresión RPG (en desarrollo)
    ├── 3.5_world_exploration/ #    Generación procedimental de mundos (en desarrollo)
    ├── 3.6_movement_camera/   #    Físicas de movimiento y cámaras kinemáticas (en desarrollo)
    └── 3.7_puzzle_stealth/    #    Puzzles, sigilo y sistemas lógicos (en desarrollo)
```

---

# ❓ Frequently Asked Questions & Troubleshooting

### 🇬🇧 English FAQ
1. **PowerShell says "Execution of scripts is disabled on this system" when activating `.venv`:**  
   Run this single command in your PowerShell window:  
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`  
   Then run `.\.venv\Scripts\Activate.ps1` again.
2. **The window opens and closes immediately:**  
   Make sure you installed Raylib by running `pip install -r requirements.txt`. You can also run any minigame with the smoke test flag to verify errors:  
   `python -B minigames/3.0_core_prototypes/space_swarm.py --smoke-test`
3. **Why do we run scripts with `python -B`?**  
   The `-B` flag tells Python not to write bytecode `.pyc` files and `__pycache__` directories, keeping the repository spotless and lightweight.
4. **My gamepad is connected, but not responding:**  
   Check the top-right corner of the window. If it shows `PAD: OFF`, reconnect your controller via USB or Bluetooth. Once detected, the badge will switch to `PAD: ON [KB/M + Pad]`.

---

### 🇪🇸 Preguntas Frecuentes en Español
1. **PowerShell dice "La ejecución de scripts está deshabilitada en este sistema" al activar `.venv`:**  
   Ejecuta este comando en la ventana de PowerShell:  
   `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`  
   Luego vuelve a ejecutar `.\.venv\Scripts\Activate.ps1`.
2. **La ventana se abre y se cierra al instante:**  
   Asegúrate de haber instalado Raylib ejecutando `pip install -r requirements.txt`. Puedes verificar si hay algún error ejecutando la prueba de integridad:  
   `python -B minigames/3.0_core_prototypes/space_swarm.py --smoke-test`
3. **¿Por qué usamos `python -B` para ejecutar?**  
   El modificador `-B` le indica a Python que no genere carpetas temporales `__pycache__` ni archivos `.pyc`, manteniendo tu carpeta de trabajo limpia y sin basura.
4. **Mi mando está conectado pero el juego no responde:**  
   Revisa la esquina superior derecha de la ventana. Si dice `PAD: OFF`, desconecta y vuelve a conectar el mando por cable USB o Bluetooth. Al detectarlo, el indicador cambiará automáticamente a `PAD: ON [KB/M + Pad]`.

---

<div align="center">

**Happy Game Programming! / ¡Feliz Programación de Videojuegos!**  
*Built with ❤️ using Python & Raylib.*

</div>
