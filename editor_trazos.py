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
from ezdxf import units, recover


class EditorTrazos:
    """Aplicación principal del editor de trazos interactivo."""
    
    # Constante de conversión: píxeles por centímetro
    # Basado en 96 DPI estándar: 96 DPI ÷ 2.54 cm/inch = 37.795 px/cm
    PIXELS_PER_CM = 37.795275591
    
    # Conversión para DXF (milímetros, estándar CNC)
    # 1 cm = 10 mm, por lo tanto: px/mm = PIXELS_PER_CM / 10
    PIXELS_PER_MM = PIXELS_PER_CM / 10.0
    
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
        clear_btn.pack(pady=5, padx=10, fill=tk.X)
        
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
                last_x, last_y = self.current_stroke[-1]
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
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
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
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
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
                        self.canvas_width_var.set(str(canvas_size["width_cm"]))
                        self.canvas_height_var.set(str(canvas_size["height_cm"]))
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
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
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
    
    def _load_dxf(self):
        """Carga trazos y formas desde un archivo DXF con soporte para entidades complejas."""
        filename = filedialog.askopenfilename(
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Intentar leer archivo DXF
                try:
                    doc = ezdxf.readfile(filename)
                except ezdxf.DXFStructureError:
                    # Intentar recuperación si el archivo está corrupto
                    doc, auditor = recover.readfile(filename)
                    if auditor.has_errors:
                        messagebox.showwarning("Advertencia", 
                            "El archivo DXF tenía errores pero se intentó recuperar.")
                
                msp = doc.modelspace()
                
                # Limpiar canvas actual
                self._clear_canvas()
                
                # Estadísticas de carga
                stats = {
                    'LWPOLYLINE': 0,
                    'POLYLINE': 0,
                    'LINE': 0,
                    'CIRCLE': 0,
                    'SPLINE': 0,
                    'ARC': 0,
                    'ELLIPSE': 0,
                    'OTHER': 0
                }
                
                # Cargar entidades DXF
                for entity in msp:
                    entity_type = entity.dxftype()
                    
                    if entity_type == 'LWPOLYLINE':
                        self._load_lwpolyline(entity)
                        stats['LWPOLYLINE'] += 1
                    
                    elif entity_type == 'POLYLINE':
                        self._load_polyline(entity)
                        stats['POLYLINE'] += 1
                    
                    elif entity_type == 'LINE':
                        self._load_line(entity)
                        stats['LINE'] += 1
                    
                    elif entity_type == 'CIRCLE':
                        self._load_circle(entity)
                        stats['CIRCLE'] += 1
                    
                    elif entity_type == 'SPLINE':
                        self._load_spline(entity)
                        stats['SPLINE'] += 1
                    
                    elif entity_type == 'ARC':
                        self._load_arc(entity)
                        stats['ARC'] += 1
                    
                    elif entity_type == 'ELLIPSE':
                        self._load_ellipse(entity)
                        stats['ELLIPSE'] += 1
                    
                    else:
                        stats['OTHER'] += 1
                
                # Mostrar estadísticas de carga
                loaded_entities = []
                for entity_type, count in stats.items():
                    if count > 0 and entity_type != 'OTHER':
                        loaded_entities.append(f"{count} {entity_type}")
                
                stats_msg = "Archivo DXF cargado correctamente.\n\n"
                if loaded_entities:
                    stats_msg += "Entidades cargadas:\n" + "\n".join(loaded_entities)
                if stats['OTHER'] > 0:
                    stats_msg += f"\n\n{stats['OTHER']} entidades no soportadas fueron ignoradas."
                
                messagebox.showinfo("Éxito", stats_msg)
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar archivo DXF: {str(e)}")
    
    def _load_lwpolyline(self, entity):
        """Carga una entidad LWPOLYLINE."""
        points_px = []
        for point in entity.get_points('xy'):
            # Convertir de mm a píxeles (invertir Y)
            x_px = point[0] * self.PIXELS_PER_MM
            y_px = -point[1] * self.PIXELS_PER_MM
            points_px.append((x_px, y_px))
        
        if len(points_px) > 1:
            # Obtener color
            color = self._aci_to_color(entity.dxf.color)
            
            # Crear trazo
            stroke_data = {
                'type': 'brush',
                'points': points_px,
                'color': color,
                'width': 2
            }
            self.strokes.append(stroke_data)
            
            # Dibujar en canvas
            for i in range(len(points_px) - 1):
                x1, y1 = points_px[i]
                x2, y2 = points_px[i + 1]
                self.canvas.create_line(x1, y1, x2, y2,
                                      fill=color,
                                      width=2,
                                      capstyle=tk.ROUND,
                                      smooth=True)
    
    def _load_polyline(self, entity):
        """Carga una entidad POLYLINE (diferente de LWPOLYLINE)."""
        points_px = []
        for vertex in entity.vertices:
            point = vertex.dxf.location
            # Convertir de mm a píxeles (invertir Y)
            x_px = point[0] * self.PIXELS_PER_MM
            y_px = -point[1] * self.PIXELS_PER_MM
            points_px.append((x_px, y_px))
        
        if len(points_px) > 1:
            # Obtener color
            color = self._aci_to_color(entity.dxf.color)
            
            # Crear trazo
            stroke_data = {
                'type': 'brush',
                'points': points_px,
                'color': color,
                'width': 2
            }
            self.strokes.append(stroke_data)
            
            # Dibujar en canvas
            for i in range(len(points_px) - 1):
                x1, y1 = points_px[i]
                x2, y2 = points_px[i + 1]
                self.canvas.create_line(x1, y1, x2, y2,
                                      fill=color,
                                      width=2,
                                      capstyle=tk.ROUND,
                                      smooth=True)
    
    def _load_line(self, entity):
        """Carga una entidad LINE."""
        start = entity.dxf.start
        end = entity.dxf.end
        
        # Convertir de mm a píxeles
        start_px = (start[0] * self.PIXELS_PER_MM, -start[1] * self.PIXELS_PER_MM)
        end_px = (end[0] * self.PIXELS_PER_MM, -end[1] * self.PIXELS_PER_MM)
        
        color = self._aci_to_color(entity.dxf.color)
        
        shape_data = {
            'type': 'line',
            'start': start_px,
            'end': end_px,
            'color': color,
            'width': 2
        }
        self.shapes.append(shape_data)
        self._draw_shape(shape_data)
    
    def _load_circle(self, entity):
        """Carga una entidad CIRCLE."""
        center = entity.dxf.center
        radius = entity.dxf.radius
        
        # Convertir de mm a píxeles
        center_px = (center[0] * self.PIXELS_PER_MM, -center[1] * self.PIXELS_PER_MM)
        radius_px = radius * self.PIXELS_PER_MM
        
        # Calcular punto final (a la derecha del centro)
        end_px = (center_px[0] + radius_px, center_px[1])
        
        color = self._aci_to_color(entity.dxf.color)
        
        shape_data = {
            'type': 'circle',
            'start': center_px,
            'end': end_px,
            'color': color,
            'width': 2
        }
        self.shapes.append(shape_data)
        self._draw_shape(shape_data)
    
    def _load_spline(self, entity):
        """Carga una entidad SPLINE convirtiéndola a polilínea."""
        try:
            # Aplanar spline a líneas con precisión de 0.5mm
            points = list(entity.flattening(distance=0.5))
            
            # Convertir a coordenadas de canvas
            points_px = []
            for point in points:
                x_px = point.x * self.PIXELS_PER_MM
                y_px = -point.y * self.PIXELS_PER_MM
                points_px.append((x_px, y_px))
            
            if len(points_px) > 1:
                # Obtener color
                color = self._aci_to_color(entity.dxf.color)
                
                # Crear trazo
                stroke_data = {
                    'type': 'brush',
                    'points': points_px,
                    'color': color,
                    'width': 2
                }
                self.strokes.append(stroke_data)
                
                # Dibujar en canvas
                for i in range(len(points_px) - 1):
                    x1, y1 = points_px[i]
                    x2, y2 = points_px[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2,
                                          fill=color,
                                          width=2,
                                          capstyle=tk.ROUND,
                                          smooth=True)
        except Exception as e:
            # Si hay error al procesar spline, ignorar silenciosamente
            print(f"Error procesando SPLINE: {e}")
    
    def _load_arc(self, entity):
        """Carga una entidad ARC convirtiéndola a polilínea."""
        try:
            center = entity.dxf.center
            radius = entity.dxf.radius
            start_angle = math.radians(entity.dxf.start_angle)
            end_angle = math.radians(entity.dxf.end_angle)
            
            # Ajustar ángulos si end_angle < start_angle
            if end_angle < start_angle:
                end_angle += 2 * math.pi
            
            # Generar puntos del arco (20 segmentos por defecto)
            num_segments = 20
            points_px = []
            for i in range(num_segments + 1):
                angle = start_angle + (end_angle - start_angle) * i / num_segments
                x = center.x + radius * math.cos(angle)
                y = center.y + radius * math.sin(angle)
                x_px = x * self.PIXELS_PER_MM
                y_px = -y * self.PIXELS_PER_MM
                points_px.append((x_px, y_px))
            
            if len(points_px) > 1:
                # Obtener color
                color = self._aci_to_color(entity.dxf.color)
                
                # Crear trazo
                stroke_data = {
                    'type': 'brush',
                    'points': points_px,
                    'color': color,
                    'width': 2
                }
                self.strokes.append(stroke_data)
                
                # Dibujar en canvas
                for i in range(len(points_px) - 1):
                    x1, y1 = points_px[i]
                    x2, y2 = points_px[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2,
                                          fill=color,
                                          width=2,
                                          capstyle=tk.ROUND,
                                          smooth=True)
        except Exception as e:
            print(f"Error procesando ARC: {e}")
    
    def _load_ellipse(self, entity):
        """Carga una entidad ELLIPSE convirtiéndola a polilínea."""
        try:
            # Aplanar elipse a líneas con precisión de 0.5mm
            points = list(entity.flattening(distance=0.5))
            
            # Convertir a coordenadas de canvas
            points_px = []
            for point in points:
                x_px = point.x * self.PIXELS_PER_MM
                y_px = -point.y * self.PIXELS_PER_MM
                points_px.append((x_px, y_px))
            
            if len(points_px) > 1:
                # Obtener color
                color = self._aci_to_color(entity.dxf.color)
                
                # Crear trazo
                stroke_data = {
                    'type': 'brush',
                    'points': points_px,
                    'color': color,
                    'width': 2
                }
                self.strokes.append(stroke_data)
                
                # Dibujar en canvas
                for i in range(len(points_px) - 1):
                    x1, y1 = points_px[i]
                    x2, y2 = points_px[i + 1]
                    self.canvas.create_line(x1, y1, x2, y2,
                                          fill=color,
                                          width=2,
                                          capstyle=tk.ROUND,
                                          smooth=True)
        except Exception as e:
            print(f"Error procesando ELLIPSE: {e}")
    
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
                
    def _clear_canvas(self):
        """Limpia todos los trazos del canvas."""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar todo el canvas?"):
            self.canvas.delete("all")
            self.strokes = []
            self.shapes = []
            
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
