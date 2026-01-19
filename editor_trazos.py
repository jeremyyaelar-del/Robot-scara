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
- Importar/exportar archivos JSON
- Diseño profesional con tonos azulados
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import json
import math


class EditorTrazos:
    """Aplicación principal del editor de trazos interactivo."""
    
    # Constante de conversión: píxeles por centímetro (aproximado)
    PIXELS_PER_CM = 37.795275591
    
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
        self.unit_type = "pixels"  # pixels o cm
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
        
        save_btn = tk.Button(left_frame, text="💾 Guardar JSON", 
                           command=self._save_json,
                           bg=self.button_color, fg="white", activebackground=self.button_active)
        save_btn.pack(pady=5, padx=10, fill=tk.X)
        
        load_btn = tk.Button(left_frame, text="📂 Cargar JSON", 
                           command=self._load_json,
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
        messagebox.showinfo("Herramienta", f"Herramienta actual: {tool}")
        
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
            else:
                self.brush_size = size_value
                
            # Actualizar el control deslizante
            if unit == "pixels":
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
        """Dibuja guías de medición en el canvas."""
        # Eliminar guías existentes
        self.canvas.delete("guide")
        
        # Obtener dimensiones del canvas
        width = int(self.canvas.cget("scrollregion").split()[2])
        height = int(self.canvas.cget("scrollregion").split()[3])
        
        # Dibujar líneas de cuadrícula cada 1 cm
        cm_px = self.PIXELS_PER_CM
        
        # Líneas verticales
        x = cm_px
        while x < width:
            self.canvas.create_line(x, 0, x, height, fill="#D0D0D0", 
                                   dash=(2, 4), tags="guide")
            x += cm_px
            
        # Líneas horizontales
        y = cm_px
        while y < height:
            self.canvas.create_line(0, y, width, y, fill="#D0D0D0", 
                                   dash=(2, 4), tags="guide")
            y += cm_px
            
        # Asegurar que las guías estén al fondo
        self.canvas.tag_lower("guide")
        
    def _on_mouse_down(self, event):
        """Maneja el evento de presionar el botón del mouse."""
        # Convertir coordenadas de ventana a canvas
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.current_tool in ["brush", "eraser"]:
            # Iniciar un nuevo trazo
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
            # Borrar dibujando en blanco
            if self.current_stroke:
                last_x, last_y = self.current_stroke[-1]
                self.canvas.create_line(last_x, last_y, x, y,
                                       fill="white",
                                       width=self.brush_size,
                                       capstyle=tk.ROUND,
                                       smooth=True)
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
        
        if self.current_tool in ["brush", "eraser"]:
            # Guardar el trazo completo
            if self.current_stroke:
                self.current_stroke.append((x, y))
                stroke_data = {
                    "type": self.current_tool,
                    "points": self.current_stroke,
                    "color": self.brush_color if self.current_tool == "brush" else "white",
                    "width": self.brush_size
                }
                self.strokes.append(stroke_data)
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
            data = {
                "canvas_size": {
                    "width_cm": float(self.canvas_width_var.get()),
                    "height_cm": float(self.canvas_height_var.get())
                },
                "strokes": self.strokes,
                "shapes": self.shapes
            }
            
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Éxito", "Archivo guardado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {str(e)}")
                
    def _load_json(self):
        """Carga trazos y formas desde un archivo JSON."""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Limpiar canvas actual
                self._clear_canvas()
                
                # Restaurar tamaño del canvas
                if "canvas_size" in data:
                    self.canvas_width_var.set(str(data["canvas_size"]["width_cm"]))
                    self.canvas_height_var.set(str(data["canvas_size"]["height_cm"]))
                    self._update_canvas_size()
                    
                # Cargar trazos
                self.strokes = data.get("strokes", [])
                for stroke in self.strokes:
                    points = stroke["points"]
                    color = stroke["color"]
                    width = stroke["width"]
                    
                    # Dibujar trazo
                    for i in range(len(points) - 1):
                        x1, y1 = points[i]
                        x2, y2 = points[i + 1]
                        self.canvas.create_line(x1, y1, x2, y2,
                                              fill=color,
                                              width=width,
                                              capstyle=tk.ROUND,
                                              smooth=True)
                        
                # Cargar formas
                self.shapes = data.get("shapes", [])
                for shape in self.shapes:
                    self._draw_shape(shape)
                    
                messagebox.showinfo("Éxito", "Archivo cargado correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar: {str(e)}")
                
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
