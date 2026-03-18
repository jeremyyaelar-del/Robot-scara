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
- Ventana "Programar" para envío de trayectorias DXF a Arduino SCARA
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import math
import threading
import time
import ezdxf
from ezdxf import units

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


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
        self._create_tool_button(tools_frame, "▭ Rectángulo", "rectangle")
        self._create_tool_button(tools_frame, "△ Triángulo", "triangle")

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

        # Separador
        ttk.Separator(left_frame, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)

        # Botón para abrir la ventana de programación SCARA
        programar_btn = tk.Button(left_frame, text="🤖 Programar",
                                  command=self._open_programar,
                                  bg="#2E7D32", fg="white", activebackground="#1B5E20",
                                  font=("Arial", 11, "bold"))
        programar_btn.pack(pady=5, padx=10, fill=tk.X)

    def _open_programar(self):
        """Abre la ventana de programación DXF/Arduino SCARA."""
        VentanaProgramar(self.root)

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
        elif self.current_tool in ["line", "circle", "rectangle", "triangle"]:
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
                # Eliminar solo elementos que NO sean guías
                for item in items:
                    tags = self.canvas.gettags(item)
                    if "guide" not in tags:
                        self.canvas.delete(item)
                        # También eliminar del almacenamiento si es necesario
                        # (esto se manejará mejor en el futuro)

                self.current_stroke.append((x, y))
        elif self.current_tool in ["line", "circle", "rectangle", "triangle"]:
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
                self.strokes.append(stroke_data)
                self.current_stroke = []
        elif self.current_tool == "eraser":
            # No guardar trazos de borrador
            self.current_stroke = []
        elif self.current_tool in ["line", "circle", "rectangle", "triangle"]:
            # Finalizar forma
            if self.shape_start:
                # Eliminar forma temporal
                if self.temp_shape:
                    self.canvas.delete(self.temp_shape)
                    self.temp_shape = None

                # Crear forma final
                shape_data = {
                    "type": self.current_tool,
                    "start": self.shape_start,
                    "end": (x, y),
                    "color": self.brush_color,
                    "width": self.brush_size
                }
                self.shapes.append(shape_data)
                self._draw_shape(shape_data)
                self.shape_start = None

    def _draw_shape_preview(self, start, end):
        """Dibuja una vista previa de la forma durante el arrastre."""
        x1, y1 = start
        x2, y2 = end

        if self.current_tool == "line":
            return self.canvas.create_line(x1, y1, x2, y2,
                                          fill=self.brush_color,
                                          width=self.brush_size)
        elif self.current_tool == "circle":
            # Calcular radio
            radius = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            return self.canvas.create_oval(x1 - radius, y1 - radius,
                                          x1 + radius, y1 + radius,
                                          outline=self.brush_color,
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

                # Crear capas para organización
                doc.layers.add('STROKES', color=7)  # Blanco
                doc.layers.add('SHAPES', color=1)   # Rojo

                # Convertir trazos a polylines DXF
                for stroke in self.strokes:
                    if stroke['type'] == 'brush':
                        # Convertir puntos de píxeles a milímetros
                        points_mm = [(x / self.PIXELS_PER_MM, -y / self.PIXELS_PER_MM)
                                    for x, y in stroke['points']]

                        if len(points_mm) > 1:
                            # Crear LWPOLYLINE para trazos
                            msp.add_lwpolyline(points_mm, dxfattribs={
                                'layer': 'STROKES',
                                'color': self._color_to_aci(stroke['color'])
                            })

                # Convertir formas a entidades DXF
                for shape in self.shapes:
                    start_x, start_y = shape['start']
                    end_x, end_y = shape['end']

                    # Convertir a milímetros (invertir Y)
                    start_mm = (start_x / self.PIXELS_PER_MM, -start_y / self.PIXELS_PER_MM)
                    end_mm = (end_x / self.PIXELS_PER_MM, -end_y / self.PIXELS_PER_MM)

                    color_aci = self._color_to_aci(shape['color'])

                    if shape['type'] == 'line':
                        msp.add_line(start_mm, end_mm, dxfattribs={
                            'layer': 'SHAPES',
                            'color': color_aci
                        })

                    elif shape['type'] == 'circle':
                        # Calcular radio
                        radius = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2) / self.PIXELS_PER_MM
                        msp.add_circle(start_mm, radius, dxfattribs={
                            'layer': 'SHAPES',
                            'color': color_aci
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
                            'color': color_aci
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
                            'color': color_aci
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

            # Redibujar guías si están activadas
            if self.show_guides.get():
                self._draw_guides()

    def run(self):
        """Inicia el bucle principal de la aplicación."""
        self.root.mainloop()




# Constantes de temporización para comunicación serial
ARDUINO_RESET_DELAY = 2.0   # segundos de espera tras reset de Arduino al conectar
SPEED_SET_DELAY = 0.05      # segundos de espera tras enviar comando de velocidad
COMMAND_INTERVAL = 0.02     # segundos entre comandos de movimiento para no saturar Arduino

class VentanaProgramar:
    """
    Ventana de programación para cargar archivos DXF y enviar trayectorias
    al robot SCARA via Arduino por puerto serial.
    """

    DEFAULT_L1 = 150.0  # mm - Longitud del brazo 1
    DEFAULT_L2 = 120.0  # mm - Longitud del brazo 2

    def __init__(self, parent):
        """
        Inicializa la ventana de programación.

        Args:
            parent: Ventana padre de Tkinter
        """
        self.window = tk.Toplevel(parent)
        self.window.title("Programar Robot SCARA")
        self.window.geometry("900x700")
        self.window.resizable(True, True)

        self.bg_color = "#E8F4F8"
        self.panel_color = "#B8D8E8"
        self.button_color = "#4A90A4"
        self.button_active = "#357A8C"
        self.window.configure(bg=self.bg_color)

        self.trajectory_mm = []
        self.trajectory_points = []
        self.serial_conn = None
        self._stop_event = threading.Event()  # Señal para detener el envío
        self._stop_event.set()  # Inicialmente no hay envío en curso
        self._send_thread = None
        self._reader_thread = None

        self.l1_var = tk.StringVar(value=str(self.DEFAULT_L1))
        self.l2_var = tk.StringVar(value=str(self.DEFAULT_L2))
        self.speed_var = tk.IntVar(value=50)
        self.port_var = tk.StringVar()

        self._build_ui()

    # ------------------------------------------------------------------ #
    # Construcción de la interfaz                                         #
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        """Construye todos los componentes de la interfaz."""
        # Barra superior
        top_frame = tk.Frame(self.window, bg=self.panel_color)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Label(top_frame, text="Programar Robot SCARA",
                 font=("Arial", 14, "bold"),
                 bg=self.panel_color, fg="#1A5A6A").pack(side=tk.LEFT, padx=10, pady=5)

        tk.Button(top_frame, text="📂 Cargar DXF",
                  command=self._load_dxf,
                  bg=self.button_color, fg="white",
                  activebackground=self.button_active).pack(side=tk.LEFT, padx=5, pady=5)

        # Controles de conexión serial
        conn_frame = tk.Frame(top_frame, bg=self.panel_color)
        conn_frame.pack(side=tk.RIGHT, padx=10, pady=5)

        tk.Label(conn_frame, text="Puerto:", bg=self.panel_color).pack(side=tk.LEFT)

        self.port_combo = ttk.Combobox(conn_frame, textvariable=self.port_var,
                                       width=10, state="readonly")
        self.port_combo.pack(side=tk.LEFT, padx=3)

        tk.Button(conn_frame, text="🔄",
                  command=self._refresh_ports,
                  bg=self.panel_color).pack(side=tk.LEFT)

        self.connect_btn = tk.Button(conn_frame, text="Conectar",
                                     command=self._toggle_connection,
                                     bg=self.button_color, fg="white",
                                     activebackground=self.button_active)
        self.connect_btn.pack(side=tk.LEFT, padx=5)

        self.status_label = tk.Label(conn_frame, text="● Desconectado",
                                     fg="#CC0000", bg=self.panel_color,
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Panel central
        center_frame = tk.Frame(self.window, bg=self.bg_color)
        center_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        traj_label_frame = tk.LabelFrame(center_frame,
                                          text="Visualización de Trayectoria",
                                          bg=self.bg_color, fg="#1A5A6A",
                                          font=("Arial", 10, "bold"))
        traj_label_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=5)

        self.traj_canvas = tk.Canvas(traj_label_frame, bg="white",
                                     highlightthickness=1,
                                     highlightbackground=self.button_color)
        self.traj_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Panel derecho
        right_frame = tk.Frame(center_frame, bg=self.bg_color, width=250)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5)
        right_frame.pack_propagate(False)

        # Configuración del robot
        config_frame = tk.LabelFrame(right_frame, text="Configuración SCARA",
                                     bg=self.bg_color, fg="#1A5A6A",
                                     font=("Arial", 10, "bold"))
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        row_l1 = tk.Frame(config_frame, bg=self.bg_color)
        row_l1.pack(fill=tk.X, padx=5, pady=3)
        tk.Label(row_l1, text="L1 (mm):", bg=self.bg_color, width=9,
                 anchor=tk.W).pack(side=tk.LEFT)
        tk.Entry(row_l1, textvariable=self.l1_var, width=8).pack(side=tk.LEFT, padx=3)

        row_l2 = tk.Frame(config_frame, bg=self.bg_color)
        row_l2.pack(fill=tk.X, padx=5, pady=3)
        tk.Label(row_l2, text="L2 (mm):", bg=self.bg_color, width=9,
                 anchor=tk.W).pack(side=tk.LEFT)
        tk.Entry(row_l2, textvariable=self.l2_var, width=8).pack(side=tk.LEFT, padx=3)

        # Velocidad
        speed_frame = tk.LabelFrame(right_frame, text="Velocidad",
                                    bg=self.bg_color, fg="#1A5A6A",
                                    font=("Arial", 10, "bold"))
        speed_frame.pack(fill=tk.X, padx=5, pady=5)

        self.speed_scale = tk.Scale(speed_frame, from_=1, to=100,
                                    orient=tk.HORIZONTAL,
                                    variable=self.speed_var,
                                    bg=self.bg_color,
                                    label="%")
        self.speed_scale.pack(fill=tk.X, padx=5, pady=3)

        # Botones de acción
        actions_frame = tk.LabelFrame(right_frame, text="Acciones",
                                      bg=self.bg_color, fg="#1A5A6A",
                                      font=("Arial", 10, "bold"))
        actions_frame.pack(fill=tk.X, padx=5, pady=5)

        self.send_btn = tk.Button(actions_frame, text="▶ Enviar a Arduino",
                                  command=self._send_trajectory,
                                  bg="#2E7D32", fg="white",
                                  activebackground="#1B5E20",
                                  font=("Arial", 10, "bold"),
                                  state=tk.DISABLED)
        self.send_btn.pack(fill=tk.X, padx=5, pady=3)

        tk.Button(actions_frame, text="⏹ Detener",
                  command=self._send_stop,
                  bg="#C62828", fg="white",
                  activebackground="#B71C1C").pack(fill=tk.X, padx=5, pady=3)

        tk.Button(actions_frame, text="🏠 Homing",
                  command=self._send_home,
                  bg=self.button_color, fg="white",
                  activebackground=self.button_active).pack(fill=tk.X, padx=5, pady=3)

        tk.Button(actions_frame, text="📍 Posición Actual",
                  command=self._request_position,
                  bg=self.button_color, fg="white",
                  activebackground=self.button_active).pack(fill=tk.X, padx=5, pady=3)

        # Área de log
        log_frame = tk.LabelFrame(right_frame, text="Log",
                                  bg=self.bg_color, fg="#1A5A6A",
                                  font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.log_text = tk.Text(log_frame, height=10, state=tk.DISABLED,
                                bg="#F0F0F0", font=("Courier", 9),
                                wrap=tk.WORD)
        log_scroll = tk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=3, pady=3)

        self._refresh_ports()

        if not SERIAL_AVAILABLE:
            self._log("⚠ pyserial no instalado. Instálalo con: pip install pyserial")
        else:
            self._log("✓ Listo. Cargue un DXF y conecte Arduino.")

    # ------------------------------------------------------------------ #
    # Utilidades de log                                                   #
    # ------------------------------------------------------------------ #

    def _log(self, message):
        """Agrega un mensaje al área de log."""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, "> " + str(message) + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------ #
    # Gestión de puertos seriales                                         #
    # ------------------------------------------------------------------ #

    def _refresh_ports(self):
        """Actualiza la lista de puertos seriales disponibles."""
        if not SERIAL_AVAILABLE:
            self.port_combo["values"] = []
            return
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.port_combo["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])

    def _toggle_connection(self):
        """Conecta o desconecta del puerto serial."""
        if not SERIAL_AVAILABLE:
            self._log("Error: pyserial no está instalado.")
            return
        if self.serial_conn and self.serial_conn.is_open:
            self._disconnect()
        else:
            self._connect()

    def _connect(self):
        """Establece conexión serial con Arduino."""
        port = self.port_var.get()
        if not port:
            self._log("Error: seleccione un puerto serial.")
            return
        try:
            self.serial_conn = serial.Serial(port, 115200, timeout=1)
            time.sleep(ARDUINO_RESET_DELAY)  # Esperar reset de Arduino
            self.connect_btn.configure(text="Desconectar")
            self.status_label.configure(text="● Conectado", fg="#007700")
            self._log("Conectado a " + port + " a 115200 baudios.")
            self._update_send_btn()
            self._reader_thread = threading.Thread(
                target=self._read_serial_loop, daemon=True)
            self._reader_thread.start()
        except serial.SerialException as e:
            self._log("Error al conectar: " + str(e))

    def _disconnect(self):
        """Cierra la conexión serial."""
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except Exception:
                pass
            self.serial_conn = None
        self.connect_btn.configure(text="Conectar")
        self.status_label.configure(text="● Desconectado", fg="#CC0000")
        self._log("Desconectado.")
        self._update_send_btn()

    def _read_serial_loop(self):
        """Hilo en segundo plano que lee respuestas del Arduino."""
        while self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline().decode("utf-8", errors="replace").strip()
                if line:
                    self.window.after(0, self._log, "Arduino: " + line)
            except (serial.SerialException, OSError):
                break

    def _send_command(self, cmd):
        """Envía un comando al Arduino por serial."""
        if not self.serial_conn or not self.serial_conn.is_open:
            self._log("Error: no hay conexión serial activa.")
            return False
        try:
            self.serial_conn.write((cmd.strip() + "\n").encode("utf-8"))
            return True
        except serial.SerialException as e:
            self._log("Error al enviar comando: " + str(e))
            return False

    # ------------------------------------------------------------------ #
    # Carga y procesamiento de DXF                                        #
    # ------------------------------------------------------------------ #

    def _load_dxf(self):
        """Abre un DXF, extrae puntos y dibuja la trayectoria."""
        filename = filedialog.askopenfilename(
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            doc = ezdxf.readfile(filename)
            msp = doc.modelspace()
            unit_scale = self._get_unit_scale(doc)

            segments = []
            for entity in msp:
                segs = self._entity_to_segments(entity, unit_scale)
                segments.extend(segs)

            if not segments:
                self._log("Advertencia: el DXF no contiene entidades reconocibles.")
                return

            self.trajectory_mm = segments
            self.trajectory_points = self._segments_to_path(segments)

            self._draw_trajectory()
            fname = filename.replace("\\", "/").split("/")[-1]
            self._log(
                "Trayectoria cargada: " + str(len(self.trajectory_points)) +
                " puntos desde \"" + fname + "\"")
            self._update_send_btn()

        except Exception as e:
            self._log("Error al cargar DXF: " + str(e))

    @staticmethod
    def _get_unit_scale(doc):
        """Devuelve factor de escala para convertir unidades DXF a mm."""
        insunits = doc.header.get("$INSUNITS", doc.units)
        unit_map = {
            units.MM: 1.0,
            units.CM: 10.0,
            units.M: 1000.0,
            units.IN: 25.4,
            units.FT: 304.8,
            0: 1.0,
        }
        return unit_map.get(insunits, 1.0)

    @staticmethod
    def _entity_to_segments(entity, unit_scale, arc_segments=64):
        """
        Convierte una entidad DXF en lista de segmentos [(x1,y1,x2,y2)] en mm.
        """
        dtype = entity.dxftype()
        pts = []

        if dtype == "LINE":
            s = entity.dxf.start
            e = entity.dxf.end
            pts = [
                (s[0] * unit_scale, s[1] * unit_scale),
                (e[0] * unit_scale, e[1] * unit_scale),
            ]

        elif dtype == "LWPOLYLINE":
            for p in entity.get_points("xy"):
                pts.append((p[0] * unit_scale, p[1] * unit_scale))

        elif dtype == "POLYLINE":
            for v in entity.vertices:
                loc = v.dxf.location
                pts.append((loc[0] * unit_scale, loc[1] * unit_scale))

        elif dtype == "CIRCLE":
            cx = entity.dxf.center[0] * unit_scale
            cy = entity.dxf.center[1] * unit_scale
            r = entity.dxf.radius * unit_scale
            for i in range(arc_segments + 1):
                angle = 2 * math.pi * i / arc_segments
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

        elif dtype == "ARC":
            cx = entity.dxf.center[0] * unit_scale
            cy = entity.dxf.center[1] * unit_scale
            r = entity.dxf.radius * unit_scale
            start_a = math.radians(entity.dxf.start_angle)
            end_a = math.radians(entity.dxf.end_angle)
            if end_a <= start_a:
                end_a += 2 * math.pi
            for i in range(arc_segments + 1):
                angle = start_a + (end_a - start_a) * i / arc_segments
                pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))

        elif dtype in ("SPLINE", "ELLIPSE"):
            try:
                for p in entity.flattening(distance=0.5):
                    pts.append((p.x * unit_scale, p.y * unit_scale))
            except Exception:
                pass

        segs = []
        for i in range(len(pts) - 1):
            segs.append((pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]))
        return segs

    @staticmethod
    def _segments_to_path(segments):
        """
        Convierte lista de segmentos en una trayectoria ordenada de puntos,
        eliminando duplicados consecutivos.
        """
        if not segments:
            return []
        path = [(segments[0][0], segments[0][1])]
        for x1, y1, x2, y2 in segments:
            if (x1, y1) != path[-1]:
                path.append((x1, y1))
            path.append((x2, y2))
        return path

    def _draw_trajectory(self):
        """Dibuja la trayectoria en el canvas de visualización."""
        self.traj_canvas.delete("all")
        if not self.trajectory_mm:
            return

        all_x = [x for x1, y1, x2, y2 in self.trajectory_mm for x in (x1, x2)]
        all_y = [y for x1, y1, x2, y2 in self.trajectory_mm for y in (y1, y2)]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)

        w = self.traj_canvas.winfo_width() or 400
        h = self.traj_canvas.winfo_height() or 300
        margin = 20

        span_x = max_x - min_x or 1
        span_y = max_y - min_y or 1
        scale = min((w - 2 * margin) / span_x, (h - 2 * margin) / span_y)

        def to_canvas(x, y):
            cx = margin + (x - min_x) * scale
            cy = h - margin - (y - min_y) * scale
            return cx, cy

        # Dibujar área de trabajo SCARA
        try:
            l1 = float(self.l1_var.get())
            l2 = float(self.l2_var.get())
            r_max = (l1 + l2) * scale
            r_min = abs(l1 - l2) * scale
            cx0, cy0 = to_canvas(0, 0)
            self.traj_canvas.create_oval(
                cx0 - r_max, cy0 - r_max, cx0 + r_max, cy0 + r_max,
                outline="#CCDDFF", dash=(4, 4))
            if r_min > 2:
                self.traj_canvas.create_oval(
                    cx0 - r_min, cy0 - r_min, cx0 + r_min, cy0 + r_min,
                    outline="#FFCCCC", dash=(4, 4))
        except (ValueError, tk.TclError):
            pass

        # Dibujar segmentos de la trayectoria
        for x1, y1, x2, y2 in self.trajectory_mm:
            px1, py1 = to_canvas(x1, y1)
            px2, py2 = to_canvas(x2, y2)
            self.traj_canvas.create_line(px1, py1, px2, py2,
                                         fill="#1A5A6A", width=1)

        # Marcar origen
        ox, oy = to_canvas(0, 0)
        r = 4
        self.traj_canvas.create_oval(ox - r, oy - r, ox + r, oy + r,
                                     fill="red", outline="red")
        self.traj_canvas.create_text(ox + 8, oy - 8, text="(0,0)",
                                     fill="red", font=("Arial", 8))

    # ------------------------------------------------------------------ #
    # Cinemática inversa SCARA                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _inverse_kinematics(x, y, l1, l2):
        """
        Calcula cinemática inversa para robot SCARA de 2 DOF.

        Args:
            x, y: Coordenada objetivo en mm
            l1: Longitud del brazo 1 en mm
            l2: Longitud del brazo 2 en mm

        Returns:
            (theta1_deg, theta2_deg) o None si el punto no es alcanzable.
        """
        d2 = x * x + y * y
        cos_theta2 = (d2 - l1 * l1 - l2 * l2) / (2.0 * l1 * l2)

        if cos_theta2 < -1.0 or cos_theta2 > 1.0:
            return None  # Fuera del espacio de trabajo

        theta2 = math.acos(cos_theta2)
        theta1 = math.atan2(y, x) - math.atan2(
            l2 * math.sin(theta2), l1 + l2 * math.cos(theta2))

        return math.degrees(theta1), math.degrees(theta2)

    # ------------------------------------------------------------------ #
    # Envío de trayectoria al Arduino                                     #
    # ------------------------------------------------------------------ #

    def _update_send_btn(self):
        """Habilita/deshabilita el botón de envío según el estado."""
        connected = bool(self.serial_conn and self.serial_conn.is_open)
        has_traj = bool(self.trajectory_points)
        sending = not self._stop_event.is_set() and self._send_thread is not None and self._send_thread.is_alive()
        state = tk.NORMAL if (connected and has_traj and not sending) else tk.DISABLED
        self.send_btn.configure(state=state)

    def _update_send_btn_sending(self, is_sending):
        """Actualiza el botón de envío durante el envío activo."""
        state = tk.DISABLED if is_sending else tk.NORMAL
        self.send_btn.configure(state=state)

    def _send_trajectory(self):
        """Envía la trayectoria al Arduino en un hilo separado."""
        if self.sending:
            return
        self._stop_event.clear()
        self._update_send_btn_sending(True)
        self._send_thread = threading.Thread(
            target=self._send_trajectory_worker, daemon=True)
        self._send_thread.start()

    def _send_trajectory_worker(self):
        """Hilo que envía comandos G0 para cada punto de la trayectoria."""
        try:
            l1 = float(self.l1_var.get())
            l2 = float(self.l2_var.get())
        except ValueError:
            self.window.after(0, self._log, "Error: L1 y L2 deben ser números.")
            self.sending = False
            self.window.after(0, self._update_send_btn)
            return

        speed = self.speed_var.get()
        self.window.after(0, self._log,
                          "Enviando " + str(len(self.trajectory_points)) +
                          " puntos (L1=" + str(l1) + " mm, L2=" + str(l2) +
                          " mm, vel=" + str(speed) + "%)...")

        self._send_command("M220 S" + str(speed))
        time.sleep(SPEED_SET_DELAY)  # Esperar que Arduino procese velocidad

        skipped = 0
        for x, y in self.trajectory_points:
            if self._stop_event.is_set():
                break
            angles = self._inverse_kinematics(x, y, l1, l2)
            if angles is None:
                skipped += 1
                continue
            theta1, theta2 = angles
            cmd = ("G0 X" + "{:.3f}".format(x) +
                   " Y" + "{:.3f}".format(y) +
                   " A" + "{:.3f}".format(theta1) +
                   " B" + "{:.3f}".format(theta2))
            if not self._send_command(cmd):
                break
            time.sleep(COMMAND_INTERVAL)  # Pausa entre comandos para no saturar buffer

        if skipped:
            self.window.after(0, self._log,
                              "Advertencia: " + str(skipped) +
                              " punto(s) fuera del espacio de trabajo.")
        self.window.after(0, self._log, "Envío completado.")
        self._stop_event.set()
        self.window.after(0, self._update_send_btn)

    def _send_stop(self):
        """Envía comando de parada al Arduino."""
        self._stop_event.set()  # Señalizar hilo de envío para que se detenga
        if self._send_command("M0"):
            self._log("Comando STOP enviado.")
        self._update_send_btn()

    def _send_home(self):
        """Envía comando de homing al Arduino."""
        if self._send_command("M100"):
            self._log("Comando HOME enviado.")

    def _request_position(self):
        """Solicita la posición actual al Arduino."""
        if self._send_command("M114"):
            self._log("Solicitud de posición enviada.")

def main():
    """Función principal para ejecutar la aplicación."""
    root = tk.Tk()
    app = EditorTrazos(root)
    app.run()


if __name__ == "__main__":
    main()