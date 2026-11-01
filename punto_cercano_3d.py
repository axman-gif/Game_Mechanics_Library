#\u00a1/usr/bin/env python3
"""
Documentaci\u00f3n Interactiva: Punto m\u00e1s cercano en un segmento BC a un punto A en 3D
Este script utiliza pyray (Raylib) para visualizar en 3D c\u00f3mo funciona el c\u00e1lculo del 
punto m\u00e1s cercano empleando la proyecci\u00f3n por producto punto y restricciones del segmento.

Controles:
- Mantener clic derecho y mover el mouse: Rotar la c\u00e1mara orbital.
- Rueda del mouse: Zoom.
- Teclas 1, 2, 3: Cambiar cu\u00e1l punto est\u00e1s moviendo (1: A, 2: B, 3: C).
- Teclas Flechas (Arriba/Abajo/Izquierda/Derecha) y ReP\u00e1g/AvP\u00e1g: Mover el punto seleccionado en los ejes X, Z e Y.
"""

from pyray import *
import math

def calcular_punto_cercano(A, B, C):
    """
    Aplica la f\u00f3rmula matem\u00e1tica detallada en la documentaci\u00f3n.
    Retorna: (Punto P b\u00fascalo, valor t original sin recortar, valor t recortado)
    """
    # 1. Vectores BA y BC
    ba_x, ba_y, ba_z = A.x - B.x, A.y - B.y, A.z - B.z
    bc_x, bc_y, bc_z = C.x - B.x, C.y - B.y, C.z - B.z
    
    # Producto punto en el numerador: \u00vec{BA} \u22c5 \u00vec{BC}
    numerador = (ba_x * bc_x) + (ba_y * bc_y) + (ba_z * bc_z)
    
    # Norma de BC al cuadrado en el denominador: ||\u00vec{BC}||^2
    denominador = (bc_x * bc_x) + (bc_y * bc_y) + (bc_z * bc_z)
    
    # Prevenir divisi\u00f3n por cero si B y C son el mismo punto
    if denominador == 0.0:
        return B, 0.0, 0.0
        
    # Calcular el par\u00e1metro t original
    t_original = numerador / denominador
    
    # 2. Aplicar restricciones del segmento
    if t_original <= 0.0:
        t_ajustado = 0.0
        caso = "Extremo B (t <= 0)"
    elif t_original >= 1.0:
        t_ajustado = 1.0
        caso = "Extremo C (t >= 1)"
    else:
        t_ajustado = t_original
        caso = "Proyecci\u00f3n Interna (0 < t < 1)"
        
    # 3. Calcular coordenadas finales del punto P
    P = Vector3(
        B.x + t_ajustado * bc_x,
        B.y + t_ajustado * bc_y,
        B.z + t_ajustado * bc_z
    )
    
    return P, t_original, t_ajustado, caso

def main():
    # Inicializaci\u00f3n de Ventana
    init_window(1280, 720, "Interactiva: Punto mas cercano en Segmento BC a Punto A")
    set_target_fps(60)
    
    # Configurar la c\u00e1mara 3D
    camera = Camera3D()
    camera.position = Vector3(10.0, 10.0, 10.0) # Posici\u00f3n inicial de la c\u00e1mara
    camera.target = Vector3(0.0, 2.0, 0.0)       # Hacia d\u00f3nde mira
    camera.up = Vector3(0.0, 1.0, 0.0)           # Vector 'arriba'
    camera.fovy = 45.0                           # Campo de visi\u00f3n
    camera.projection = CAMERA_PERSPECTIVE
    
    # Puntos iniciales en el espacio 3D
    A = Vector3(2.0, 5.0, 1.0)
    B = Vector3(-3.0, 1.0, -2.0)
    C = Vector3(3.0, 2.0, 3.0)
    
    seleccionado = 1 # 1: A, 2: B, 3: C
    
    while not window_should_close():
        # --- ENTRADAS Y CONTROL DE PUNTOS ---
        if is_key_pressed(KEY_ONE): seleccionado = 1
        if is_key_pressed(KEY_TWO): seleccionado = 2
        if is_key_pressed(KEY_THREE): seleccionado = 3
        
        # Obtener el punto actualmente seleccionado para modificarlo
        pt_mod = A if seleccionado == 1 else (B if seleccionado == 2 else C)
        step = 0.1
        
        # Mover en X y Z con las Flechas del Teclado
        if is_key_down(KEY_LEFT): pt_mod.x -= step
        if is_key_down(KEY_RIGHT): pt_mod.x += step
        if is_key_down(KEY_UP): pt_mod.z -= step
        if is_key_down(KEY_DOWN): pt_mod.z += step
        # Mover en Y (Altura) con ReP\u00e1g y AvP\u00e1g
        if is_key_down(KEY_PAGE_UP): pt_mod.y += step
        if is_key_down(KEY_PAGE_DOWN): pt_mod.y -= step
        
        # Actualizar valores de vuelta en las variables correspondientes
        if seleccionado == 1: A = pt_mod
        elif seleccionado == 2: B = pt_mod
        else: C = pt_mod
        
        # Actualizar c\u00e1mara orbital por defecto con el mouse (clic derecho para rotar)
        update_camera(camera, CAMERA_ORBITAL)
        
        # --- C\u00c1LCULOS GEOM\u00c9TRICOS ---
        P, t_orig, t_ajust, caso = calcular_punto_cercano(A, B, C)
        
        # Calcular el punto proyectado matem\u00e1tico continuo (sin recortar al segmento)
        P_linea = Vector3(
            B.x + t_orig * (C.x - B.x),
            B.y + t_orig * (C.y - B.y),
            B.z + t_orig * (C.z - B.z)
        )
        
        # --- DIBUJADO DE LA ESCENA ---
        begin_drawing()
        clear_background(RAYWHITE)
        
        # Iniciar modo 3D
        begin_mode_3d(camera)
        
        # Plano cartesiano de referencia (Grilla en el suelo Y = 0)
        draw_grid(20, 1.0)
        
        # Dibujar Ejes del Plano Cartesiano (X: Rojo, Y: Verde, Z: Azul)
        draw_line_3d(Vector3(-10, 0, 0), Vector3(10, 0, 0), RED)
        draw_line_3d(Vector3(0, -10, 0), Vector3(0, 10, 0), GREEN)
        draw_line_3d(Vector3(0, 0, -10), Vector3(0, 0, 10), BLUE)
        
        # Dibujar la recta infinita como una l\u00ednea tenue gris
        # Extendemos visualmente la direcci\u00f3n para entender la proyecci\u00f3n infinita
        dir_x, dir_y, dir_z = C.x - B.x, C.y - B.y, C.z - B.z
        linea_extend_ini = Vector3(B.x - dir_x * 5, B.y - dir_y * 5, B.z - dir_z * 5)
        linea_extend_fin = Vector3(C.x + dir_x * 5, C.y + dir_y * 5, C.z + dir_z * 5)
        draw_line_3d(linea_extend_ini, linea_extend_fin, LIGHTGRAY)
        
        # Dibujar Segmento Real BC (L\u00ednea gruesa negra o azul oscuro)
        draw_line_3d(B, C, DARKBLUE)
        
        # Dibujar l\u00ednea discontinua conceptual desde A hasta su proyecci\u00f3n ideal en la recta
        draw_line_3d(A, P_linea, GRAY)
        
        # Dibujar l\u00ednea roja desde A hasta el punto m\u00e1s cercano final P (Distancia m\u00ednima)
        draw_line_3d(A, P, RED)
        
        # Dibujar Esferas indicativas de los puntos
        draw_sphere(A, 0.2, RED)       # Punto A
        draw_sphere(B, 0.2, DARKBLUE)  # Extremo B
        draw_sphere(C, 0.2, DARKBLUE)  # Extremo C
        draw_sphere(P, 0.15, GOLD)     # Punto m\u00e1s cercano P
        
        # Texto en el espacio 3D para identificar los puntos
        draw_text_3d(get_font_default(), "A", Vector3(A.x, A.y + 0.3, A.z), 0.4, 0.05, 0.0, RED, False)
        draw_text_3d(get_font_default(), "B", Vector3(B.x, B.y + 0.3, B.z), 0.4, 0.05, 0.0, DARKBLUE, False)
        draw_text_3d(get_font_default(), "C", Vector3(C.x, C.y + 0.3, C.z), 0.4, 0.05, 0.0, DARKBLUE, False)
        draw_text_3d(get_font_default(), "P (Mas cercano)", Vector3(P.x, P.y - 0.4, P.z), 0.4, 0.05, 0.0, ORANGE, False)
        
        end_mode_3d()
        
        # --- INTERFAZ EN 2D (DOCUMENTACI\u00d3N SUPERPUESTA) ---
        draw_rectangle(10, 10, 480, 310, fade(SKYBLUE, 0.3))
        draw_rectangle_lines(10, 10, 480, 310, BLUE)
        
        draw_text("DOCUMENTACION & GEOMETRIA", 20, 20, 16, BLACK)
        
        # F\u00f3rmulas textuales
        draw_text("Formula del parametro de proyeccion:", 20, 45, 13, DARKGRAY)
        draw_text("t = (BA . BC) / ||BC||^2", 30, 65, 14, MAROON)
        draw_text("Punto final restringido:", 20, 90, 13, DARKGRAY)
        draw_text("P = B + t_ajustado * BC", 30, 110, 14, MAROON)
        
        # Valores en tiempo real
        draw_text(f"Punto A: ({A.x:.2f}, {A.y:.2f}, {A.z:.2f})", 20, 140, 13, BLACK)
        draw_text(f"Punto B: ({B.x:.2f}, {B.y:.2f}, {B.z:.2f})", 20, 160, 13, BLACK)
        draw_text(f"Punto C: ({C.x:.2f}, {C.y:.2f}, {C.z:.2f})", 20, 180, 13, BLACK)
        
        # Datos de Proyecci\u00f3n
        draw_text(f"t calculado (original): {t_orig:.4f}", 20, 210, 13, DARKGREEN)
        draw_text(f"t ajustado (segmento): {t_ajust:.4f}", 20, 230, 13, DARKGREEN)
        draw_text(f"Caso: {caso}", 20, 250, 14, ORANGE)
        draw_text(f"P calculado: ({P.x:.2f}, {P.y:.2f}, {P.z:.2f})", 20, 280, 14, RED)
        
        # Instrucciones de controles en la esquina inferior izquierda
        draw_rectangle(10, 580, 500, 130, fade(LIGHTGRAY, 0.8))
        draw_text("CONTROLES DE SELECCION Y MOVIMIENTO:", 20, 590, 12, BLACK)
        draw_text(f"[1, 2, 3] para seleccionar punto. ACTUAL: Punto {'A' if seleccionado==1 else ('B' if seleccionado==2 else 'C')}", 20, 610, 12, MAROON)
        draw_text("Flechas [Izquierda/Derecha]: Mover en eje X", 20, 630, 12, DARKGRAY)
        draw_text("Flechas [Arriba/Abajo]: Mover en eje Z", 20, 650, 12, DARKGRAY)
        draw_text("[RePag / AvPag]: Mover en eje Y (Altura)", 20, 670, 12, DARKGRAY)
        draw_text("Clic Derecho + Arrastrar Mouse: Rotar entorno 3D", 20, 690, 12, DARKGRAY)
        
        end_drawing()
        
    close_window()

if __name__ == "__main__":
    main()
