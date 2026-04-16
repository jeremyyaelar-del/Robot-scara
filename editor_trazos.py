#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Editor de Trazos Interactivo
Aplicación profesional de edición de trazos con características avanzadas
usando Python y Tkinter.

Características:
- Canvas editable con trazos de mouse
- Herramientas de edición: grosor, borrador, formas básicas
- Configuración del lienzo: tamaño ajustable, guías de medición
- Importar/exportar archivos DXF (compatible con CNC)
- Diseño profesional con tonos azulados
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import math
import ezdxf
from ezdxf import units


class EditorTrazos:
    """Aplicación principal del editor de trazos interactivo."""

    # Constante de conversión: píxeles por centímetro
    # Basado en 96 DPI estándar: 96 DPI ÷ 2.54 cm/inch = 37.795 px/cm
    PIXELS_PER_CM = 37.795275591

    # Conversión para DXF (milímetros, estándar CNC)
    # 1 cm = 10 mm, por lo tanto: px/mm = PIXELS_PER_CM / 10
    PIXELS_PER_MM = PIXELS_PER_CM / 10.0

    # Precisión para curvas DXF (SPLINE/ELLIPSE/ARC)
    FLATTENING_DISTANCE = 0.5  # mm
    ARC_SEGMENTS = 64

    # Umbral para detectar puntos colineales en círculo por 3 puntos
    COLLINEARITY_THRESHOLD = 1e-10

    def __init__(self, root):
        """
        Inicializa la aplicación del editor de trazos.

        Args:
            root: Ventana principal de Tkinter
        """
        self.root = root
        self.root.title("Editor de Trazos Interactivo")
        self.root.geometry("1200x800")

        # Variables de estado
        self.current_tool = "brush"  # brush, eraser, line, circle, rectangle, triangle
        self.brush_size = 2  # en píxeles
        self.brush_color = "#000000"
        self.canvas_width_cm = 30
        self.canvas_height_cm = 20
        self.show_guides = tk.BooleanVar(value=True)

        # Almacenamiento de trazos y formas
        self.strokes = []  # Lista de trazos libres
        self.shapes = []  # Lista de formas geométricas
        self.current_stroke = []  # Trazo actual en progreso
        self.temp_shape = None  # Forma temporal durante el dibujo
        self.shape_start = None  # Punto inicial para formas

        # Diámetro fijo para herramienta círculo
        self.circle_diameter_var = tk.StringVar(value="5")

        # Estado para herramienta círculo por 3 puntos
        self.circle3p_points = []
        self.circle3p_markers = []

        # Líneas fantasmas de seguimiento (entre trazos, no aparecen en DXF)
        self.ghost_lines = []
        self.last_end_point = None
        self.show_ghost_lines = tk.BooleanVar(value=True)

        # Configurar la interfaz de usuario
        self._setup_ui()
        self._setup_canvas()
        self._bind_events()

    def _setup_ui(self):
        """Configura la interfaz de usuario con diseño profesional azulado."""
        # Colores del tema azulado profesional
        self.bg_color = "#E8F4F8"
        self.panel_color = "#B8D8E8"
        self.button_color = "#4A90A4"
        self.button_active = "#357A8C"

        self.root.configure(bg=self.bg_color)

        # Panel superior - Herramientas principales
        top_frame = tk.Frame(self.root, bg=self.panel_color, height=80)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        top_frame.pack_propagate(False)

        # Título
        title_label = tk.Label(top_frame, text="Editor de Trazos Interactivo",
                              font=("Arial", 16, "bold"), bg=self.panel_color, fg="#1A5A6A")
        title_label.pack(pady=5)

        # Frame de botones de herramientas
        tools_frame = tk.Frame(top_frame, bg=self.panel_color)
        tools_frame.pack(pady=5)

        # Botones de herramientas
        self._create_tool_button(tools_frame, "✏️ Pincel", "brush")
        self._create_tool_button(tools_frame, "🗑️ Borrador", "eraser")
        self._create_tool_button(tools_frame, "📏 Línea", "line")
        self._create_tool_button(tools_frame, "⭕ Círculo", "circle")
        self._create_tool_button(tools_frame, "⭕ Círculo 3P", "circle3p")
        self._create_tool_button(tools_frame, "▭ Rectángulo", "rectangle")
        self._create_tool_button(tools_frame, "△ Triángulo", "triangle")

        # Botón de alternancia para líneas fantasmas
        self.ghost_btn = tk.Button(
            tools_frame, text="👁 Líneas Fantasma ✓",
            command=self._toggle_ghost_lines,
            bg=self.button_color, fg="white",
            activebackground=self.button_active,
            width=18, height=1
        )
        self.ghost_btn.pack(side=tk.LEFT, padx=3)

        # Panel izquierdo - Configuración
        left_frame = tk.Frame(self.root, bg=self.panel_color, width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        left_frame.pack_propagate(False)

        # Sección de grosor
        self._create_section_label(left_frame, "Grosor del Trazo")

        size_frame = tk.Frame(left_frame, bg=self.panel_color)
        size_frame.pack(pady=5, padx=10, fill=tk.X)

        self.size_var = tk.StringVar(value="2")
        size_entry = tk.Entry(size_frame, textvariable=self.size_var, width=8)
        size_entry.pack(side=tk.LEFT, padx=5)

        # Selector de unidades
        self.unit_var = tk.StringVar(value="pixels")
        unit_menu = ttk.Combobox(size_frame, textvariable=self.unit_var,
                                values=["pixels", "cm"], width=8, state="readonly")
        unit_menu.pack(side=tk.LEFT, padx=5)
        unit_menu.bind("<<ComboboxSelected>>", self._update_brush_size)

        size_entry.bind("<Return>", self._update_brush_size)

        # Control deslizante de grosor
        self.size_scale = tk.Scale(left_frame, from_=1, to=50, orient=tk.HORIZONTAL,
                                   bg=self.panel_color, command=self._on_size_scale)
        self.size_scale.set(2)
        self.size_scale.pack(pady=5, padx=10, fill=tk.X)

        # Sección de diámetro para herramienta círculo
        self._create_section_label(left_frame, "Diámetro Círculo (cm)")

        diameter_frame = tk.Frame(left_frame, bg=self.panel_color)
        diameter_frame.pack(pady=5, padx=10, fill=tk.X)

        diameter_entry = tk.Entry(diameter_frame, textvariable=self.circle_diameter_var, width=10)
        diameter_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(diameter_frame, text="cm", bg=self.panel_color).pack(side=tk.LEFT)

        # Sección de color
        self._create_section_label(left_frame, "Color")

        color_frame = tk.Frame(left_frame, bg=self.panel_color)
        color_frame.pack(pady=5, padx=10, fill=tk.X)

        self.color_display = tk.Canvas(color_frame, width=30, height=30,
                                       bg=self.brush_color, highlightthickness=1)
        self.color_display.pack(side=tk.LEFT, padx=5)

        color_btn = tk.Button(color_frame, text="Elegir Color",
                            command=self._choose_color,
                            bg=self.button_color, fg="white", activebackground=self.button_active)
        color_btn.pack(side=tk.LEFT, padx=5)

        # Sección de configuración del canvas
        self._create_section_label(left_frame, "Tamaño del Lienzo (cm)")

        canvas_size_frame = tk.Frame(left_frame, bg=self.panel_color)
        canvas_size_frame.pack(pady=5, padx=10, fill=tk.X)

        tk.Label(canvas_size_frame, text="Ancho:", bg=self.panel_color).pack(side=tk.LEFT)
        self.canvas_width_var = tk.StringVar(value="30")
        width_entry = tk.Entry(canvas_size_frame, textvariable=self.canvas_width_var, width=6)
        width_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(canvas_size_frame, text="Alto:", bg=self.panel_color).pack(side=tk.LEFT)
        self.canvas_height_var = tk.StringVar(value="20")
        height_entry = tk.Entry(canvas_size_frame, textvariable=self.canvas_height_var, width=6)
        height_entry.pack(side=tk.LEFT, padx=5)

        apply_size_btn = tk.Button(left_frame, text="Aplicar Tamaño",
                                   command=self._update_canvas_size,
                                   bg=self.button_color, fg="white", activebackground=self.button_active)
        apply_size_btn.pack(pady=5, padx=10, fill=tk.X)

        # Guías de medición
        guides_check = tk.Checkbutton(left_frame, text="Mostrar Guías de Medición",
                                     variable=self.show_guides, command=self._toggle_guides,
                                     bg=self.panel_color, selectcolor=self.button_color)
        guides_check.pack(pady=5, padx=10)

        # Separador
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)

        # Botones de archivo
        self._create_section_label(left_frame, "Archivo")

        save_btn = tk.Button(left_frame, text="💾 Guardar DXF",
                           command=self._save_dxf,
                           bg=self.button_color, fg="white", activebackground=self.button_active)
        save_btn.pack(pady=5, padx=10, fill=tk.X)

        load_btn = tk.Button(left_frame, text="📂 Cargar DXF",
                           command=self._load_dxf,
                           bg=self.button_color, fg="white", activebackground=self.button_active)
        load_btn.pack(pady=5, padx=10, fill=tk.X)

        clear_btn = tk.Button(left_frame, text="🗑️ Limpiar Todo",
                            command=self._clear_canvas,
                            bg="#D84A4A", fg="white", activebackground="#B83838")
        clear_btn.pack(pady=5, padx=10)

    def _create_tool_button(self, parent, text, tool):
        """Crea un botón de herramienta con estilo."""
        btn = tk.Button(parent, text=text, command=lambda: self._set_tool(tool),
                       bg=self.button_color, fg="white", activebackground=self.button_active,
                       width=12, height=1)
        btn.pack(side=tk.LEFT, padx=3)
        return btn

    def _create_section_label(self, parent, text):
        """Crea una etiqueta de sección."""
        label = tk.Label(parent, text=text, font=("Arial", 11, "bold"),
                        bg=self.panel_color, fg="#1A5A6A")
        label.pack(pady=(10, 5), padx=10)
        return label

    def _setup_canvas(self):
        """Configura el canvas principal con barras de desplazamiento."""
        # Frame contenedor para canvas y scrollbars
        canvas_frame = tk.Frame(self.root, bg=self.bg_color)
        canvas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Scrollbars
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Canvas principal
        self.canvas = tk.Canvas(canvas_frame, bg="white",
                               xscrollcommand=h_scrollbar.set,
                               yscrollcommand=v_scrollbar.set,
                               highlightthickness=1, highlightbackground="#4A90A4")
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Configurar scrollbars
        h_scrollbar.config(command=self.canvas.xview)
        v_scrollbar.config(command=self.canvas.yview)

        # Configurar tamaño inicial del canvas
        self._update_canvas_size()

    def _bind_events(self):
        """Vincula eventos del mouse al canvas."""
        self.canvas.bind("<Button-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def _set_tool(self, tool):
        """Establece la herramienta actual."""
        self.current_tool = tool
        # Actualizar visualmente sin diálogos molestos
        # En una versión futura, se podría resaltar el botón activo

    def _on_size_scale(self, value):
        """Actualiza el tamaño del pincel desde el control deslizante."""
        self.size_var.set(value)
        self._update_brush_size()

    def _update_brush_size(self, event=None):
        """Actualiza el tamaño del pincel según la unidad seleccionada."""
        try:
            size_value = float(self.size_var.get())
            unit = self.unit_var.get()

            if unit == "cm":
                # Convertir cm a píxeles
                self.brush_size = size_value * self.PIXELS_PER_CM
                # Actualizar el control deslizante al valor en píxeles
                self.size_scale.set(int(self.brush_size))
            else:
                self.brush_size = size_value
                # Actualizar el control deslizante
                self.size_scale.set(int(size_value))
        except ValueError:
            pass

    def _choose_color(self):
        """Abre el diálogo de selección de color."""
        color = colorchooser.askcolor(initialcolor=self.brush_color)[1]
        if color:
            self.brush_color = color
            self.color_display.configure(bg=color)

    def _update_canvas_size(self):
        """Actualiza el tamaño del canvas según las dimensiones en cm."""
        try:
            width_cm = float(self.canvas_width_var.get())
            height_cm = float(self.canvas_height_var.get())

            # Convertir cm a píxeles
            width_px = int(width_cm * self.PIXELS_PER_CM)
            height_px = int(height_cm * self.PIXELS_PER_CM)

            # Configurar la región de desplazamiento del canvas
            self.canvas.config(scrollregion=(0, 0, width_px, height_px))

            # Redibujar guías si están activadas
            if self.show_guides.get():
                self._draw_guides()
        except ValueError:
            messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos.")

    def _toggle_guides(self):
        """Activa o desactiva las guías de medición."""
        if self.show_guides.get():
            self._draw_guides()
        else:
            # Eliminar guías
            self.canvas.delete("guide")

    def _draw_guides(self):
        """Dibuja guías de medición en el canvas con numeración cartesiana."""
        # Eliminar guías existentes
        self.canvas.delete("guide")

        # Obtener dimensiones del canvas
        scrollregion = self.canvas.cget("scrollregion")
        if not scrollregion:
            return

        parts = scrollregion.split()
        if len(parts) < 4:
            return

        width = int(parts[2])
        height = int(parts[3])

        # Dibujar líneas de cuadrícula cada 1 cm
        cm_px = self.PIXELS_PER_CM

        # Ejes principales (X=0 e Y=0) más gruesos
        # Eje Y (vertical) en x=0
        self.canvas.create_line(0, 0, 0, height, fill="#808080",
                               width=2, tags="guide")
        # Eje X (horizontal) en y=height (invertido porque Y crece hacia abajo en canvas)
        self.canvas.create_line(0, height, width, height, fill="#808080",
                               width=2, tags="guide")

        # Etiquetas de los ejes
        self.canvas.create_text(width - 10, height - 10, text="X",
                               fill="#404040", font=("Arial", 10, "bold"),
                               tags="guide")
        self.canvas.create_text(10, 10, text="Y",
                               fill="#404040", font=("Arial", 10, "bold"),
                               tags="guide")

        # Líneas verticales con numeración
        x = cm_px
        cm_count = 1
        while x < width:
            self.canvas.create_line(x, 0, x, height, fill="#D0D0D0",
                                   dash=(2, 4), tags="guide")
            # Etiqueta con el valor en cm
            self.canvas.create_text(x, height - 5, text=str(cm_count),
                                   fill="#606060", font=("Arial", 8),
                                   anchor=tk.N, tags="guide")
            x += cm_px
            cm_count += 1

        # Líneas horizontales con numeración (invertida porque Y crece hacia abajo)
        y = height - cm_px
        cm_count = 1
        while y > 0:
            self.canvas.create_line(0, y, width, y, fill="#D0D0D0",
                                   dash=(2, 4), tags="guide")
            # Etiqueta con el valor en cm
            self.canvas.create_text(5, y, text=str(cm_count),
                                   fill="#606060", font=("Arial", 8),
                                   anchor=tk.W, tags="guide")
            y -= cm_px
            cm_count += 1

        # Asegurar que las guías estén al fondo
        self.canvas.tag_lower("guide")

    def _on_mouse_down(self, event):
        """Maneja el evento de presionar el botón del mouse."""
        # Convertir coordenadas de ventana a canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.current_tool == "brush":
            # Iniciar un nuevo trazo
            self.current_stroke = [(x, y)]
        elif self.current_tool == "eraser":
            # Iniciar borrado
            self.current_stroke = [(x, y)]
        elif self.current_tool == "circle":
            # Crear círculo inmediatamente con diámetro fijo al hacer clic
            try:
                diameter_cm = float(self.circle_diameter_var.get())
                if diameter_cm <= 0:
                    raise ValueError("El diámetro debe ser mayor que cero")
            except ValueError:
                diameter_cm = 5.0
                self.circle_diameter_var.set("5")
                messagebox.showwarning(
                    "Valor inválido",
                    "El diámetro ingresado no es válido. Se usará 5 cm por defecto."
                )
            radius_px = (diameter_cm / 2) * self.PIXELS_PER_CM
            shape_data = {
                "type": "circle",
                "start": (x, y),
                "end": (x + radius_px, y),
                "color": self.brush_color,
                "width": self.brush_size
            }
            self.shapes.append(shape_data)
            self._draw_shape(shape_data)
            self._add_to_draw_sequence((x, y), (x, y))
        elif self.current_tool == "circle3p":
            self._handle_circle3p_click(x, y)
        elif self.current_tool in ["line", "rectangle", "triangle"]:
            # Guardar punto inicial para formas
            self.shape_start = (x, y)

    def _on_mouse_drag(self, event):
        """Maneja el evento de arrastrar el mouse."""
        # Convertir coordenadas de ventana a canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.current_tool == "brush":
            # Dibujar línea desde el último punto
            if self.current_stroke:
                last_x, last_y = self.current_stroke[-1]
                line = self.canvas.create_line(last_x, last_y, x, y,
                                              fill=self.brush_color,
                                              width=self.brush_size,
                                              capstyle=tk.ROUND,
                                              smooth=True)
                self.current_stroke.append((x, y))
        elif self.current_tool == "eraser":
            # Borrar elementos encontrados (excepto guías)
            if self.current_stroke:
                # Buscar elementos en el área del borrador
                # Usar un radio basado en el tamaño del brush
                radius = self.brush_size / 2
                items = self.canvas.find_overlapping(
                    x - radius, y - radius,
                    x + radius, y + radius
                )
                # Eliminar solo elementos que NO sean guías ni fantasmas
                for item in items:
                    tags = self.canvas.gettags(item)
                    if "guide" not in tags and "ghost" not in tags:
                        self.canvas.delete(item)
                        # También eliminar del almacenamiento si es necesario
                        # (esto se manejará mejor en el futuro)

                self.current_stroke.append((x, y))
        elif self.current_tool in ["line", "rectangle", "triangle"]:
            # Dibujar forma temporal
            if self.shape_start:
                # Eliminar forma temporal anterior
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)

                # Dibujar nueva forma temporal
                self.temp_shape = self._draw_shape_preview(self.shape_start, (x, y))

    def _on_mouse_up(self, event):
        """Maneja el evento de soltar el botón del mouse."""
        # Convertir coordenadas de ventana a canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        if self.current_tool == "brush":
            # Guardar el trazo completo
            if self.current_stroke:
                self.current_stroke.append((x, y))
                stroke_data = {
                    "type": self.current_tool,
                    "points": self.current_stroke,
                    "color": self.brush_color,
                    "width": self.brush_size
                }
                start_pt = self.current_stroke[0]
                end_pt = self.current_stroke[-1]
                self.strokes.append(stroke_data)
                self.current_stroke = []
                self._add_to_draw_sequence(start_pt, end_pt)
        elif self.current_tool == "eraser":
            # No guardar trazos de borrador
            self.current_stroke = []
        elif self.current_tool in ["line", "rectangle", "triangle"]:
            # Finalizar forma
            if self.shape_start:
                # Eliminar forma temporal
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                    self.temp_shape = None

                start_pt = self.shape_start
                # Crear forma final
                shape_data = {
                    "type": self.current_tool,
                    "start": start_pt,
                    "end": (x, y),
                    "color": self.brush_color,
                    "width": self.brush_size
                }
                self.shapes.append(shape_data)
                self._draw_shape(shape_data)
                self.shape_start = None
                self._add_to_draw_sequence(start_pt, (x, y))

    def _draw_shape_preview(self, start, end):
        """Dibuja una vista previa de la forma durante el arrastre."""
        x1, y1 = start
        x2, y2 = end

        if self.current_tool == "line":
            return self.canvas.create_line(x1, y1, x2, y2,
                                          fill=self.brush_color,
                                          width=self.brush_size)
        elif self.current_tool == "rectangle":
            return self.canvas.create_rectangle(x1, y1, x2, y2,
                                               outline=self.brush_color,
                                               width=self.brush_size)
        elif self.current_tool == "triangle":
            # Triángulo isósceles
            mid_x = (x1 + x2) / 2
            points = [mid_x, y1, x1, y2, x2, y2]
            return self.canvas.create_polygon(points, outline=self.brush_color,
                                             fill="", width=self.brush_size)
        return None

    def _draw_shape(self, shape_data):
        """Dibuja una forma en el canvas."""
        shape_type = shape_data["type"]
        start = shape_data["start"]
        end = shape_data["end"]
        color = shape_data["color"]
        width = shape_data["width"]

        x1, y1 = start
        x2, y2 = end

        if shape_type == "line":
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width)
        elif shape_type == "circle":
            radius = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            self.canvas.create_oval(x1 - radius, y1 - radius,
                                   x1 + radius, y1 + radius,
                                   outline=color, width=width)
        elif shape_type == "rectangle":
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=width)
        elif shape_type == "triangle":
            mid_x = (x1 + x2) / 2
            points = [mid_x, y1, x1, y2, x2, y2]
            self.canvas.create_polygon(points, outline=color, fill="", width=width)

    # ------------------------------------------------------------------
    # Herramienta: Círculo por 3 puntos
    # ------------------------------------------------------------------

    def _handle_circle3p_click(self, x, y):
        """Maneja los clics para la herramienta de círculo por 3 puntos."""
        marker_size = 5
        marker = self.canvas.create_oval(
            x - marker_size, y - marker_size,
            x + marker_size, y + marker_size,
            fill=self.brush_color, outline=self.brush_color,
            tags="circle3p_marker"
        )
        self.circle3p_markers.append(marker)
        self.circle3p_points.append((x, y))

        if len(self.circle3p_points) == 3:
            p1, p2, p3 = self.circle3p_points
            result = self._circle_from_3_points(p1, p2, p3)

            if result:
                cx, cy, r = result
                shape_data = {
                    "type": "circle",
                    "start": (cx, cy),
                    "end": (cx + r, cy),
                    "color": self.brush_color,
                    "width": self.brush_size
                }
                self.shapes.append(shape_data)
                self._draw_shape(shape_data)
                self._add_to_draw_sequence((cx, cy), (cx, cy))
            else:
                messagebox.showwarning(
                    "Advertencia",
                    "Los 3 puntos son colineales. No se puede crear un círculo."
                )

            # Limpiar marcadores y resetear estado
            for marker in self.circle3p_markers:
                self.canvas.delete(marker)
            self.circle3p_markers = []
            self.circle3p_points = []

    def _circle_from_3_points(self, p1, p2, p3):
        """Calcula el círculo que pasa por 3 puntos. Devuelve (cx, cy, r) o None."""
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3

        # Sistema de ecuaciones: x²+y²+Dx+Ey+F=0
        # Resolver con regla de Cramer
        a_mat = [[x1, y1, 1], [x2, y2, 1], [x3, y3, 1]]
        b_vec = [-(x1**2 + y1**2), -(x2**2 + y2**2), -(x3**2 + y3**2)]

        det = (a_mat[0][0] * (a_mat[1][1]*a_mat[2][2] - a_mat[1][2]*a_mat[2][1]) -
               a_mat[0][1] * (a_mat[1][0]*a_mat[2][2] - a_mat[1][2]*a_mat[2][0]) +
               a_mat[0][2] * (a_mat[1][0]*a_mat[2][1] - a_mat[1][1]*a_mat[2][0]))

        if abs(det) < self.COLLINEARITY_THRESHOLD:
            return None

        det_d = (b_vec[0] * (a_mat[1][1]*a_mat[2][2] - a_mat[1][2]*a_mat[2][1]) -
                 a_mat[0][1] * (b_vec[1]*a_mat[2][2] - a_mat[1][2]*b_vec[2]) +
                 a_mat[0][2] * (b_vec[1]*a_mat[2][1] - a_mat[1][1]*b_vec[2]))

        det_e = (a_mat[0][0] * (b_vec[1]*a_mat[2][2] - a_mat[1][2]*b_vec[2]) -
                 b_vec[0] * (a_mat[1][0]*a_mat[2][2] - a_mat[1][2]*a_mat[2][0]) +
                 a_mat[0][2] * (a_mat[1][0]*b_vec[2] - b_vec[1]*a_mat[2][0]))

        det_f = (a_mat[0][0] * (a_mat[1][1]*b_vec[2] - b_vec[1]*a_mat[2][1]) -
                 a_mat[0][1] * (a_mat[1][0]*b_vec[2] - b_vec[1]*a_mat[2][0]) +
                 b_vec[0] * (a_mat[1][0]*a_mat[2][1] - a_mat[1][1]*a_mat[2][0]))

        d_coef = det_d / det
        e_coef = det_e / det
        f_coef = det_f / det

        cx = -d_coef / 2
        cy = -e_coef / 2
        discriminant = cx**2 + cy**2 - f_coef
        if discriminant < 0:
            return None
        r = math.sqrt(discriminant)
        return cx, cy, r

    # ------------------------------------------------------------------
    # Líneas fantasmas de seguimiento
    # ------------------------------------------------------------------

    def _add_to_draw_sequence(self, start_pt, end_pt):
        """Registra un nuevo elemento y dibuja la línea fantasma desde el punto anterior."""
        if self.last_end_point is not None:
            ghost = (self.last_end_point, start_pt)
            self.ghost_lines.append(ghost)
            if self.show_ghost_lines.get():
                item = self.canvas.create_line(
                    ghost[0][0], ghost[0][1], ghost[1][0], ghost[1][1],
                    fill="#AAAAAA", width=1, dash=(6, 4), tags="ghost"
                )
                self.canvas.tag_lower("ghost")
        self.last_end_point = end_pt

    def _toggle_ghost_lines(self):
        """Alterna la visibilidad de las líneas fantasmas de seguimiento."""
        self.show_ghost_lines.set(not self.show_ghost_lines.get())
        if self.show_ghost_lines.get():
            self.ghost_btn.config(text="👁 Líneas Fantasma ✓")
            self._redraw_ghost_lines()
        else:
            self.ghost_btn.config(text="👁 Líneas Fantasma ✗")
            self.canvas.delete("ghost")

    def _redraw_ghost_lines(self):
        """Redibuja todas las líneas fantasmas almacenadas."""
        self.canvas.delete("ghost")
        if not self.show_ghost_lines.get():
            return
        for from_pt, to_pt in self.ghost_lines:
            self.canvas.create_line(
                from_pt[0], from_pt[1], to_pt[0], to_pt[1],
                fill="#AAAAAA", width=1, dash=(6, 4), tags="ghost"
            )
        if self.ghost_lines:
            self.canvas.tag_lower("ghost")

    def _save_json(self):
        """Guarda los trazos y formas en un archivo JSON."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.")]
        )

        if filename:
            try:
                # Validar que los valores del canvas sean numéricos
                width_cm = float(self.canvas_width_var.get())
                height_cm = float(self.canvas_height_var.get())

                data = {
                    "canvas_size": {
                        "width_cm": width_cm,
                        "height_cm": height_cm
                    },
                    "strokes": self.strokes,
                    "shapes": self.shapes
                }

                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", "Archivo guardado correctamente.")
            except ValueError as e:
                messagebox.showerror("Error", f"Valores de tamaño de canvas inválidos: {str(e)}")
            except (IOError, PermissionError) as e:
                messagebox.showerror("Error", f"Error al guardar archivo: {str(e)}")
            except (TypeError, ValueError) as e:
                messagebox.showerror("Error", f"Error al serializar datos: {str(e)}")

    def _load_json(self):
        """Carga trazos y formas desde un archivo JSON."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.")]
        )

        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Validar estructura básica del JSON
                if not isinstance(data, dict):
                    raise ValueError("El archivo JSON debe contener un objeto")

                # Limpiar canvas actual
                self._clear_canvas()

                # Restaurar tamaño del canvas
                if "canvas_size" in data and isinstance(data["canvas_size"], dict):
                    canvas_size = data["canvas_size"]
                    if "width_cm" in canvas_size and "height_cm" in canvas_size:
                        self.canvas_width_var.set(str(canvas_size["width_cm" ]))
                        self.canvas_height_var.set(str(canvas_size["height_cm" ]))
                        self._update_canvas_size()

                # Cargar trazos con validación
                self.strokes = []
                for stroke in data.get("strokes", []):
                    if not isinstance(stroke, dict):
                        continue
                    if not all(key in stroke for key in ["points", "color", "width"]):
                        continue

                    # Validar y agregar el trazo
                    self.strokes.append(stroke)

                    # Dibujar trazo en el canvas
                    points = stroke["points"]
                    color = stroke["color"]
                    width = stroke["width"]

                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i + 1]
                        self.canvas.create_line(x1, y1, x2, y2,
                                              fill=color,
                                              width=width,
                                              capstyle=tk.ROUND,
                                              smooth=True)

                # Cargar formas con validación
                self.shapes = []
                for shape in data.get("shapes", []):
                    if not isinstance(shape, dict):
                        continue
                    if not all(key in shape for key in ["type", "start", "end", "color", "width"]):
                        continue

                    self.shapes.append(shape)
                    self._draw_shape(shape)

                messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
            except (IOError, PermissionError) as e:
                messagebox.showerror("Error", f"Error al leer archivo: {str(e)}")
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Error al decodificar JSON: {str(e)}")
            except (ValueError, KeyError, TypeError) as e:
                messagebox.showerror("Error", f"Formato de archivo inválido: {str(e)}")

    def _save_dxf(self):
        """Guarda los trazos y formas en un archivo DXF compatible con CNC."""
        filename = filedialog.asksaveasfilename(
            defaultextension=".dxf",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.")]
        )

        if filename:
            try:
                # Crear nuevo documento DXF (R2010 es compatible con la mayoría de CNCs)
                doc = ezdxf.new('R2010', setup=True)
                msp = doc.modelspace()

                # Configurar unidades en milímetros (estándar para CNC)
                doc.units = units.MM

                # Crear capas para organización (color uniforme ACI=7 para todos los trazos)
                doc.layers.add('STROKES', color=7)
                doc.layers.add('SHAPES', color=7)

                # Convertir trazos a polylines DXF
                for stroke in self.strokes:
                    if stroke['type'] == 'brush':
                        # Convertir puntos de píxeles a milímetros
                        points_mm = [(x / self.PIXELS_PER_MM, -y / self.PIXELS_PER_MM)
                                    for x, y in stroke['points']]

                        if len(points_mm) > 1:
                            # Crear LWPOLYLINE para trazos (color uniforme)
                            msp.add_lwpolyline(points_mm, dxfattribs={
                                'layer': 'STROKES',
                                'color': 7
                            })

                # Convertir formas a entidades DXF
                for shape in self.shapes:
                    start_x, start_y = shape['start']
                    end_x, end_y = shape['end']

                    # Convertir a milímetros (invertir Y)
                    start_mm = (start_x / self.PIXELS_PER_MM, -start_y / self.PIXELS_PER_MM)
                    end_mm = (end_x / self.PIXELS_PER_MM, -end_y / self.PIXELS_PER_MM)

                    if shape['type'] == 'line':
                        msp.add_line(start_mm, end_mm, dxfattribs={
                            'layer': 'SHAPES',
                            'color': 7
                        })

                    elif shape['type'] == 'circle':
                        # Calcular radio desde start (centro) hasta end (punto en circunferencia)
                        radius = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2) / self.PIXELS_PER_MM
                        msp.add_circle(start_mm, radius, dxfattribs={
                            'layer': 'SHAPES',
                            'color': 7
                        })

                    elif shape['type'] == 'rectangle':
                        # Crear rectángulo como polyline cerrada
                        top_left = start_mm
                        bottom_right = end_mm
                        points = [
                            top_left,
                            (bottom_right[0], top_left[1]),
                            bottom_right,
                            (top_left[0], bottom_right[1]),
                            top_left  # Cerrar
                        ]
                        msp.add_lwpolyline(points, close=True, dxfattribs={
                            'layer': 'SHAPES',
                            'color': 7
                        })

                    elif shape['type'] == 'triangle':
                        # Calcular puntos del triángulo
                        mid_x = (start_x + end_x) / 2
                        points_mm = [
                            (mid_x / self.PIXELS_PER_MM, -start_y / self.PIXELS_PER_MM),
                            (start_x / self.PIXELS_PER_MM, -end_y / self.PIXELS_PER_MM),
                            (end_x / self.PIXELS_PER_MM, -end_y / self.PIXELS_PER_MM),
                            (mid_x / self.PIXELS_PER_MM, -start_y / self.PIXELS_PER_MM)  # Cerrar
                        ]
                        msp.add_lwpolyline(points_mm, close=True, dxfattribs={
                            'layer': 'SHAPES',
                            'color': 7
                        })

                # Guardar archivo DXF
                doc.saveas(filename)
                messagebox.showinfo("Éxito", "Archivo DXF guardado correctamente para CNC.")

            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar archivo DXF: {str(e)}")

    def _get_unit_scale_to_mm(self, doc):
        """Convierte las unidades del DXF a milímetros."""
        insunits = doc.header.get("$INSUNITS", doc.units)
        unit_map = {
            units.MM: 1.0,
            units.CM: 10.0,
            units.M: 1000.0,
            units.IN: 25.4,
            units.FT: 304.8,
            0: 1.0,  # Unitless
        }
        return unit_map.get(insunits, 1.0)

    def _iter_entity_points_mm(self, entity, unit_scale):
        """Devuelve puntos (x,y) en mm para calcular bbox y dibujar curvas."""
        points = []
        dtype = entity.dxftype()

        if dtype == "LWPOLYLINE":
            for point in entity.get_points("xy"):
                points.append((point[0] * unit_scale, point[1] * unit_scale))

        elif dtype == "POLYLINE":
            for vertex in entity.vertices:
                loc = vertex.dxf.location
                points.append((loc[0] * unit_scale, loc[1] * unit_scale))

        elif dtype == "LINE":
            start = entity.dxf.start
            end = entity.dxf.end
            points.append((start[0] * unit_scale, start[1] * unit_scale))
            points.append((end[0] * unit_scale, end[1] * unit_scale))

        elif dtype == "CIRCLE":
            center = entity.dxf.center
            radius = entity.dxf.radius * unit_scale
            cx = center[0] * unit_scale
            cy = center[1] * unit_scale
            points.extend([
                (cx - radius, cy - radius),
                (cx + radius, cy + radius),
                (cx - radius, cy + radius),
                (cx + radius, cy - radius),
            ])

        elif dtype == "ARC":
            center = entity.dxf.center
            radius = entity.dxf.radius * unit_scale
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            for i in range(self.ARC_SEGMENTS + 1):
                angle = start_angle + (end_angle - start_angle) * i / self.ARC_SEGMENTS
                x = (center[0] * unit_scale) + radius * math.cos(angle)
                y = (center[1] * unit_scale) + radius * math.sin(angle)
                points.append((x, y))

        elif dtype in ("SPLINE", "ELLIPSE"):
            try:
                for point in entity.flattening(distance=self.FLATTENING_DISTANCE):
                    points.append((point.x * unit_scale, point.y * unit_scale))
            except Exception:
                pass

        return points

    def _to_canvas(self, x_mm, y_mm, min_x, max_y, margin_x, margin_y):
        """Convierte coordenadas en mm a coordenadas de canvas (px)."""
        x_px = (x_mm - min_x + margin_x) * self.PIXELS_PER_MM
        y_px = (max_y - y_mm + margin_y) * self.PIXELS_PER_MM
        return x_px, y_px

    def _load_dxf(self):
        """Carga trazos y formas desde un archivo DXF."""
        filename = filedialog.askopenfilename(
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.")]
        )

        if filename:
            try:
                doc = ezdxf.readfile(filename)
                msp = doc.modelspace()

                unit_scale = self._get_unit_scale_to_mm(doc)

                # 1) Bounding box robusto
                min_x = min_y = float("inf")
                max_x = max_y = float("-inf")

                for entity in msp:
                    for x, y in self._iter_entity_points_mm(entity, unit_scale):
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)

                # Fallback a EXTMIN/EXTMAX si no hubo puntos válidos
                if min_x == float("inf"):
                    extmin = doc.header.get("$EXTMIN")
                    extmax = doc.header.get("$EXTMAX")
                    if extmin and extmax:
                        min_x = extmin.x * unit_scale
                        min_y = extmin.y * unit_scale
                        max_x = extmax.x * unit_scale
                        max_y = extmax.y * unit_scale
                    else:
                        messagebox.showwarning("Advertencia", "El archivo DXF está vacío o no contiene entidades válidas.")
                        return

                # 2) Ajuste de canvas con margen
                MARGIN_PERCENT = 0.1
                width_mm = max_x - min_x
                height_mm = max_y - min_y
                margin_x = width_mm * MARGIN_PERCENT
                margin_y = height_mm * MARGIN_PERCENT

                new_width_cm = (width_mm + 2 * margin_x) / 10
                new_height_cm = (height_mm + 2 * margin_y) / 10

                self.canvas_width_var.set(str(int(new_width_cm)))
                self.canvas_height_var.set(str(int(new_height_cm)))
                self._update_canvas_size()

                # 3) Limpiar canvas sin confirmar
                self._clear_canvas(confirm=False)

                # 4) Dibujar entidades
                for entity in msp:
                    dtype = entity.dxftype()

                    if dtype in ("LWPOLYLINE", "POLYLINE", "SPLINE", "ARC", "ELLIPSE"):
                        points_mm = self._iter_entity_points_mm(entity, unit_scale)
                        points_px = [
                            self._to_canvas(x, y, min_x, max_y, margin_x, margin_y)
                            for x, y in points_mm
                        ]
                        if len(points_px) > 1:
                            color = self._aci_to_color(entity.dxf.color)
                            stroke_data = {
                                "type": "brush",
                                "points": points_px,
                                "color": color,
                                "width": 2
                            }
                            self.strokes.append(stroke_data)
                            for i in range(len(points_px) - 1):
                                x1, y1 = points_px[i]
                                x2, y2 = points_px[i + 1]
                                self.canvas.create_line(
                                    x1, y1, x2, y2,
                                    fill=color,
                                    width=2,
                                    capstyle=tk.ROUND,
                                    smooth=True
                                )

                    elif dtype == "LINE":
                        start = entity.dxf.start
                        end = entity.dxf.end
                        start_mm = (start[0] * unit_scale, start[1] * unit_scale)
                        end_mm = (end[0] * unit_scale, end[1] * unit_scale)

                        start_px = self._to_canvas(*start_mm, min_x, max_y, margin_x, margin_y)
                        end_px = self._to_canvas(*end_mm, min_x, max_y, margin_x, margin_y)

                        color = self._aci_to_color(entity.dxf.color)
                        shape_data = {
                            "type": "line",
                            "start": start_px,
                            "end": end_px,
                            "color": color,
                            "width": 2
                        }
                        self.shapes.append(shape_data)
                        self._draw_shape(shape_data)

                    elif dtype == "CIRCLE":
                        center = entity.dxf.center
                        radius = entity.dxf.radius * unit_scale
                        center_mm = (center[0] * unit_scale, center[1] * unit_scale)

                        center_px = self._to_canvas(*center_mm, min_x, max_y, margin_x, margin_y)
                        end_px = self._to_canvas(center_mm[0] + radius, center_mm[1], min_x, max_y, margin_x, margin_y)

                        color = self._aci_to_color(entity.dxf.color)
                        shape_data = {
                            "type": "circle",
                            "start": center_px,
                            "end": end_px,
                            "color": color,
                            "width": 2
                        }
                        self.shapes.append(shape_data)
                        self._draw_shape(shape_data)

                messagebox.showinfo("Éxito", "Archivo DXF cargado correctamente.")

            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar archivo DXF: {str(e)}")

    def _color_to_aci(self, hex_color):
        """Convierte color hexadecimal a AutoCAD Color Index (ACI)."""
        # Mapeo básico de colores comunes
        color_map = {
            '#000000': 7,   # Blanco (en AutoCAD, negro se muestra como blanco)
            '#FF0000': 1,   # Rojo
            '#FFFF00': 2,   # Amarillo
            '#00FF00': 3,   # Verde
            '#00FFFF': 4,   # Cyan
            '#0000FF': 5,   # Azul
            '#FF00FF': 6,   # Magenta
            '#FFFFFF': 7,   # Blanco
        }
        return color_map.get(hex_color.upper(), 7)  # Por defecto blanco

    def _aci_to_color(self, aci):
        """Convierte AutoCAD Color Index (ACI) a color hexadecimal."""
        # Mapeo inverso
        aci_map = {
            1: '#FF0000',  # Rojo
            2: '#FFFF00',  # Amarillo
            3: '#00FF00',  # Verde
            4: '#00FFFF',  # Cyan
            5: '#0000FF',  # Azul
            6: '#FF00FF',  # Magenta
            7: '#000000',  # Negro (blanco en AutoCAD)
        }
        return aci_map.get(aci, '#000000')  # Por defecto negro

    def _clear_canvas(self, confirm=True):
        """Limpia todos los trazos del canvas."""
        if not confirm or messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar todo el canvas?"):
            self.canvas.delete("all")
            self.strokes = []
            self.shapes = []

            # Resetear estado de líneas fantasmas
            self.ghost_lines = []
            self.last_end_point = None

            # Resetear estado de círculo 3 puntos
            self.circle3p_points = []
            self.circle3p_markers = []

            # Redibujar guías si están activadas
            if self.show_guides.get():
                self._draw_guides()

    def run(self):
        """Inicia el bucle principal de la aplicación."""
        self.root.mainloop()


def main():
    """Función principal para ejecutar la aplicación."""
    root = tk.Tk()
    app = EditorTrazos(root)
    app.run()


if __name__ == "__main__":
    main()