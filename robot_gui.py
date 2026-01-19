#!/usr/bin/env python3
"""
Advanced GUI for SCARA Robot Drawing
Provides freehand and geometric drawing modes, file loading, line width adjustment, and zoom functionality.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import math


class RobotDrawingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Robot SCARA - GUI Avanzada de Dibujo")
        
        # Canvas settings
        self.canvas_width = 800
        self.canvas_height = 600
        self.zoom_level = 1.0
        self.zoom_min = 0.1
        self.zoom_max = 5.0
        
        # Drawing state
        self.drawing_mode = "freehand"  # freehand, line, rectangle, circle
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        self.start_x = None
        self.start_y = None
        self.temp_item = None
        
        # Line settings
        self.line_width = 2
        self.line_width_unit = "px"  # px or mm
        self.line_color = "black"
        
        # Storage for drawn items
        self.drawn_items = []
        self.loaded_paths = []
        
        # Pixels per millimeter (approximate, can be calibrated)
        self.px_per_mm = 3.78  # ~96 DPI
        
        self.setup_ui()
        self.bind_events()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Control panel (top)
        control_frame = ttk.LabelFrame(main_frame, text="Controles", padding="10")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Drawing mode selection
        ttk.Label(control_frame, text="Modo de Dibujo:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.mode_var = tk.StringVar(value="freehand")
        modes = [
            ("Mano Alzada", "freehand"),
            ("Línea Recta", "line"),
            ("Rectángulo", "rectangle"),
            ("Círculo", "circle")
        ]
        for i, (text, mode) in enumerate(modes):
            ttk.Radiobutton(control_frame, text=text, variable=self.mode_var, 
                          value=mode, command=self.change_mode).grid(row=0, column=i+1, padx=5)
        
        # Line width controls
        ttk.Label(control_frame, text="Grosor:").grid(row=1, column=0, padx=5, sticky=tk.W, pady=5)
        self.width_var = tk.DoubleVar(value=2)
        width_spinbox = ttk.Spinbox(control_frame, from_=0.1, to=50, increment=0.5, 
                                   textvariable=self.width_var, width=10,
                                   command=self.update_line_width)
        width_spinbox.grid(row=1, column=1, padx=5)
        
        # Unit selection
        self.unit_var = tk.StringVar(value="px")
        ttk.Radiobutton(control_frame, text="píxeles (px)", variable=self.unit_var, 
                       value="px", command=self.update_line_width).grid(row=1, column=2, padx=5)
        ttk.Radiobutton(control_frame, text="milímetros (mm)", variable=self.unit_var, 
                       value="mm", command=self.update_line_width).grid(row=1, column=3, padx=5)
        
        # File operations
        file_frame = ttk.Frame(control_frame)
        file_frame.grid(row=2, column=0, columnspan=5, pady=5)
        ttk.Button(file_frame, text="Cargar Archivo JSON", 
                  command=self.load_path_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="Limpiar Canvas", 
                  command=self.clear_canvas).pack(side=tk.LEFT, padx=5)
        
        # Zoom info
        self.zoom_label = ttk.Label(control_frame, text="Zoom: 100%")
        self.zoom_label.grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Label(control_frame, text="(Ctrl + para acercar, Ctrl - para alejar)").grid(
            row=3, column=2, columnspan=3, pady=5, sticky=tk.W)
        
        # Canvas with scrollbars
        canvas_frame = ttk.Frame(main_frame)
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create canvas
        self.canvas = tk.Canvas(canvas_frame, width=self.canvas_width, 
                               height=self.canvas_height, bg="white", 
                               cursor="crosshair")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.status_label = ttk.Label(status_frame, text="Listo", relief=tk.SUNKEN)
        self.status_label.pack(fill=tk.X, pady=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
    
    def bind_events(self):
        """Bind mouse and keyboard events"""
        # Mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Keyboard events for zoom
        self.root.bind("<Control-plus>", self.zoom_in)
        self.root.bind("<Control-equal>", self.zoom_in)  # For keyboards without numpad
        self.root.bind("<Control-minus>", self.zoom_out)
    
    def change_mode(self):
        """Change drawing mode"""
        self.drawing_mode = self.mode_var.get()
        mode_names = {
            "freehand": "Mano Alzada",
            "line": "Línea Recta",
            "rectangle": "Rectángulo",
            "circle": "Círculo"
        }
        self.update_status(f"Modo cambiado a: {mode_names[self.drawing_mode]}")
    
    def update_line_width(self):
        """Update line width based on current settings"""
        value = self.width_var.get()
        unit = self.unit_var.get()
        
        if unit == "mm":
            # Convert mm to pixels
            self.line_width = value * self.px_per_mm
            self.line_width_unit = "mm"
        else:
            self.line_width = value
            self.line_width_unit = "px"
        
        self.update_status(f"Grosor de línea: {value} {unit}")
    
    def get_scaled_coords(self, x, y):
        """Get coordinates scaled by zoom level"""
        return x / self.zoom_level, y / self.zoom_level
    
    def on_mouse_down(self, event):
        """Handle mouse button press"""
        self.is_drawing = True
        self.last_x, self.last_y = self.get_scaled_coords(event.x, event.y)
        self.start_x, self.start_y = self.last_x, self.last_y
    
    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        if not self.is_drawing:
            return
        
        x, y = self.get_scaled_coords(event.x, event.y)
        
        if self.drawing_mode == "freehand":
            # Draw line segment
            line = self.canvas.create_line(
                self.last_x * self.zoom_level, self.last_y * self.zoom_level,
                x * self.zoom_level, y * self.zoom_level,
                width=self.line_width * self.zoom_level,
                fill=self.line_color,
                capstyle=tk.ROUND,
                smooth=True
            )
            self.drawn_items.append(line)
            self.last_x, self.last_y = x, y
        
        else:
            # For geometric shapes, show preview
            if self.temp_item:
                self.canvas.delete(self.temp_item)
            
            if self.drawing_mode == "line":
                self.temp_item = self.canvas.create_line(
                    self.start_x * self.zoom_level, self.start_y * self.zoom_level,
                    x * self.zoom_level, y * self.zoom_level,
                    width=self.line_width * self.zoom_level,
                    fill=self.line_color
                )
            
            elif self.drawing_mode == "rectangle":
                self.temp_item = self.canvas.create_rectangle(
                    self.start_x * self.zoom_level, self.start_y * self.zoom_level,
                    x * self.zoom_level, y * self.zoom_level,
                    outline=self.line_color,
                    width=self.line_width * self.zoom_level
                )
            
            elif self.drawing_mode == "circle":
                # Calculate radius
                radius = math.sqrt((x - self.start_x)**2 + (y - self.start_y)**2)
                self.temp_item = self.canvas.create_oval(
                    (self.start_x - radius) * self.zoom_level,
                    (self.start_y - radius) * self.zoom_level,
                    (self.start_x + radius) * self.zoom_level,
                    (self.start_y + radius) * self.zoom_level,
                    outline=self.line_color,
                    width=self.line_width * self.zoom_level
                )
    
    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if not self.is_drawing:
            return
        
        self.is_drawing = False
        
        # For geometric shapes, finalize the shape
        if self.drawing_mode in ["line", "rectangle", "circle"] and self.temp_item:
            self.drawn_items.append(self.temp_item)
            self.temp_item = None
    
    def zoom_in(self, event=None):
        """Zoom in the canvas"""
        if self.zoom_level < self.zoom_max:
            old_zoom = self.zoom_level
            self.zoom_level = min(self.zoom_level * 1.2, self.zoom_max)
            self.apply_zoom(old_zoom)
            self.update_status(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def zoom_out(self, event=None):
        """Zoom out the canvas"""
        if self.zoom_level > self.zoom_min:
            old_zoom = self.zoom_level
            self.zoom_level = max(self.zoom_level / 1.2, self.zoom_min)
            self.apply_zoom(old_zoom)
            self.update_status(f"Zoom: {int(self.zoom_level * 100)}%")
    
    def apply_zoom(self, old_zoom):
        """Apply zoom transformation to all items"""
        scale = self.zoom_level / old_zoom
        self.canvas.scale("all", 0, 0, scale, scale)
        self.zoom_label.config(text=f"Zoom: {int(self.zoom_level * 100)}%")
    
    def load_path_file(self):
        """Load a path from a JSON file"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de trazado",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Support different JSON formats
            if "points" in data:
                self.draw_points(data["points"])
            elif "lines" in data:
                self.draw_lines(data["lines"])
            elif "paths" in data:
                self.draw_paths(data["paths"])
            else:
                messagebox.showerror("Error", "Formato de archivo no reconocido")
                return
            
            self.update_status(f"Archivo cargado: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar archivo: {str(e)}")
    
    def draw_points(self, points):
        """Draw a series of connected points"""
        if len(points) < 2:
            return
        
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            line = self.canvas.create_line(
                p1["x"] * self.zoom_level, p1["y"] * self.zoom_level,
                p2["x"] * self.zoom_level, p2["y"] * self.zoom_level,
                width=self.line_width * self.zoom_level,
                fill="blue"
            )
            self.loaded_paths.append(line)
    
    def draw_lines(self, lines):
        """Draw individual line segments"""
        for line_data in lines:
            line = self.canvas.create_line(
                line_data["x1"] * self.zoom_level, line_data["y1"] * self.zoom_level,
                line_data["x2"] * self.zoom_level, line_data["y2"] * self.zoom_level,
                width=self.line_width * self.zoom_level,
                fill="blue"
            )
            self.loaded_paths.append(line)
    
    def draw_paths(self, paths):
        """Draw multiple paths"""
        for path in paths:
            if "points" in path:
                self.draw_points(path["points"])
    
    def clear_canvas(self):
        """Clear all drawings from canvas"""
        self.canvas.delete("all")
        self.drawn_items.clear()
        self.loaded_paths.clear()
        self.update_status("Canvas limpiado")
    
    def update_status(self, message):
        """Update status bar message"""
        self.status_label.config(text=message)


def main():
    root = tk.Tk()
    app = RobotDrawingGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
