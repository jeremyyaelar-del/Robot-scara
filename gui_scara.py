#!/usr/bin/env python3
"""
GUI for Robot SCARA
Enhanced interface with centimeter-based canvas, scrollbars, and elegant design
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
from datetime import datetime


class ScaraGUI:
    """Main GUI class for SCARA robot interface"""
    
    # Conversion factor: 1 cm = 37.8 pixels
    CM_TO_PIXELS = 37.8
    
    def __init__(self, root):
        self.root = root
        self.root.title("Robot SCARA - Interfaz de Control")
        self.root.geometry("1000x700")
        
        # Canvas dimensions in centimeters
        self.canvas_width_cm = 50
        self.canvas_height_cm = 40
        
        # Drawing settings
        self.line_thickness = 2
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Store coordinates in centimeters
        self.coordinates_cm = []
        self.current_path = []
        
        # Color scheme - elegant and modern
        self.bg_color = "#2C3E50"  # Dark blue-gray
        self.canvas_bg = "#ECF0F1"  # Light gray
        self.accent_color = "#3498DB"  # Bright blue
        self.button_color = "#34495E"  # Darker gray
        self.text_color = "#ECF0F1"  # Light text
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        self.root.configure(bg=self.bg_color)
        
        # Top frame for controls
        self.create_control_panel()
        
        # Canvas frame with scrollbars
        self.create_canvas_area()
        
        # Bottom status bar
        self.create_status_bar()
        
    def create_control_panel(self):
        """Create the control panel with buttons and settings"""
        control_frame = tk.Frame(self.root, bg=self.bg_color, padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Title label
        title_label = tk.Label(
            control_frame,
            text="Robot SCARA - Control de Trayectorias",
            font=("Helvetica", 16, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        title_label.pack(pady=(0, 10))
        
        # Buttons frame
        buttons_frame = tk.Frame(control_frame, bg=self.bg_color)
        buttons_frame.pack()
        
        # Create styled buttons
        button_style = {
            'font': ('Helvetica', 10, 'bold'),
            'bg': self.button_color,
            'fg': self.text_color,
            'activebackground': self.accent_color,
            'activeforeground': self.text_color,
            'relief': tk.RAISED,
            'bd': 2,
            'padx': 15,
            'pady': 8,
            'cursor': 'hand2'
        }
        
        self.clear_btn = tk.Button(
            buttons_frame,
            text="Limpiar Canvas",
            command=self.clear_canvas,
            **button_style
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(
            buttons_frame,
            text="Guardar Coordenadas",
            command=self.save_coordinates,
            **button_style
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.resize_btn = tk.Button(
            buttons_frame,
            text="Ajustar Tamaño",
            command=self.resize_canvas_dialog,
            **button_style
        )
        self.resize_btn.pack(side=tk.LEFT, padx=5)
        
        self.thickness_btn = tk.Button(
            buttons_frame,
            text="Grosor de Línea",
            command=self.set_line_thickness,
            **button_style
        )
        self.thickness_btn.pack(side=tk.LEFT, padx=5)
        
        # Settings display
        settings_frame = tk.Frame(control_frame, bg=self.bg_color)
        settings_frame.pack(pady=(10, 0))
        
        self.settings_label = tk.Label(
            settings_frame,
            text=self.get_settings_text(),
            font=("Helvetica", 9),
            bg=self.bg_color,
            fg=self.text_color
        )
        self.settings_label.pack()
        
    def create_canvas_area(self):
        """Create the canvas with scrollbars"""
        # Frame to contain canvas and scrollbars
        canvas_container = tk.Frame(self.root, bg=self.bg_color)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas
        self.canvas = tk.Canvas(
            canvas_container,
            bg=self.canvas_bg,
            highlightthickness=2,
            highlightbackground=self.accent_color
        )
        
        # Create scrollbars
        v_scrollbar = ttk.Scrollbar(
            canvas_container,
            orient=tk.VERTICAL,
            command=self.canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_container,
            orient=tk.HORIZONTAL,
            command=self.canvas.xview
        )
        
        # Configure canvas scrolling
        self.canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # Grid layout for canvas and scrollbars
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        # Set canvas scroll region
        self.update_canvas_size()
        
        # Bind mouse events for drawing
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.canvas.bind("<Motion>", self.update_cursor_position)
        
        # Draw grid
        self.draw_grid()
        
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = tk.Frame(self.root, bg=self.button_color, relief=tk.SUNKEN)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = tk.Label(
            status_frame,
            text="Listo | Posición: (0.0, 0.0) cm | Puntos guardados: 0",
            font=("Helvetica", 9),
            bg=self.button_color,
            fg=self.text_color,
            anchor=tk.W,
            padx=10
        )
        self.status_label.pack(fill=tk.X)
        
    def get_settings_text(self):
        """Get current settings as text"""
        return (f"Canvas: {self.canvas_width_cm} × {self.canvas_height_cm} cm | "
                f"Grosor: {self.line_thickness}px | "
                f"Escala: 1 cm = {self.CM_TO_PIXELS} píxeles")
        
    def update_canvas_size(self):
        """Update canvas size based on cm dimensions"""
        width_px = int(self.canvas_width_cm * self.CM_TO_PIXELS)
        height_px = int(self.canvas_height_cm * self.CM_TO_PIXELS)
        
        self.canvas.configure(scrollregion=(0, 0, width_px, height_px))
        self.canvas.configure(width=min(800, width_px), height=min(500, height_px))
        
    def draw_grid(self):
        """Draw grid lines on canvas (1 cm spacing)"""
        # Clear existing grid
        self.canvas.delete("grid")
        
        width_px = int(self.canvas_width_cm * self.CM_TO_PIXELS)
        height_px = int(self.canvas_height_cm * self.CM_TO_PIXELS)
        
        # Draw vertical lines every cm
        for cm in range(int(self.canvas_width_cm) + 1):
            x = cm * self.CM_TO_PIXELS
            self.canvas.create_line(
                x, 0, x, height_px,
                fill="#BDC3C7",
                width=1,
                tags="grid"
            )
            
        # Draw horizontal lines every cm
        for cm in range(int(self.canvas_height_cm) + 1):
            y = cm * self.CM_TO_PIXELS
            self.canvas.create_line(
                0, y, width_px, y,
                fill="#BDC3C7",
                width=1,
                tags="grid"
            )
            
        # Draw axis labels
        for cm in range(0, int(self.canvas_width_cm) + 1, 5):
            x = cm * self.CM_TO_PIXELS
            self.canvas.create_text(
                x, 10,
                text=f"{cm}cm",
                fill="#7F8C8D",
                font=("Helvetica", 8),
                tags="grid"
            )
            
        for cm in range(0, int(self.canvas_height_cm) + 1, 5):
            y = cm * self.CM_TO_PIXELS
            self.canvas.create_text(
                10, y,
                text=f"{cm}cm",
                fill="#7F8C8D",
                font=("Helvetica", 8),
                tags="grid"
            )
            
        # Send grid to back
        self.canvas.tag_lower("grid")
        
    def pixels_to_cm(self, pixels):
        """Convert pixels to centimeters"""
        return round(pixels / self.CM_TO_PIXELS, 2)
        
    def cm_to_pixels(self, cm):
        """Convert centimeters to pixels"""
        return cm * self.CM_TO_PIXELS
        
    def start_draw(self, event):
        """Start drawing"""
        self.drawing = True
        # Get actual canvas coordinates (accounting for scroll)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        self.last_x = x
        self.last_y = y
        
        # Start new path
        self.current_path = []
        
        # Add point to current path (in cm)
        x_cm = self.pixels_to_cm(x)
        y_cm = self.pixels_to_cm(y)
        self.current_path.append([x_cm, y_cm])
        
    def draw(self, event):
        """Draw on canvas"""
        if not self.drawing:
            return
            
        # Get actual canvas coordinates (accounting for scroll)
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.last_x is not None and self.last_y is not None:
            # Draw continuous line with specified thickness
            self.canvas.create_line(
                self.last_x, self.last_y, x, y,
                fill="#E74C3C",  # Red color for drawn lines
                width=self.line_thickness,
                capstyle=tk.ROUND,
                smooth=True,
                tags="drawing"
            )
            
        # Add point to current path (in cm)
        x_cm = self.pixels_to_cm(x)
        y_cm = self.pixels_to_cm(y)
        self.current_path.append([x_cm, y_cm])
        
        self.last_x = x
        self.last_y = y
        
    def stop_draw(self, event):
        """Stop drawing"""
        self.drawing = False
        
        # Save current path to coordinates
        if len(self.current_path) > 1:
            self.coordinates_cm.append(self.current_path.copy())
            self.update_status()
            
        self.current_path = []
        self.last_x = None
        self.last_y = None
        
    def update_cursor_position(self, event):
        """Update cursor position in status bar"""
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        x_cm = self.pixels_to_cm(x)
        y_cm = self.pixels_to_cm(y)
        
        total_points = sum(len(path) for path in self.coordinates_cm)
        self.status_label.configure(
            text=f"Listo | Posición: ({x_cm}, {y_cm}) cm | Puntos guardados: {total_points}"
        )
        
    def update_status(self):
        """Update status bar"""
        total_points = sum(len(path) for path in self.coordinates_cm)
        self.status_label.configure(
            text=f"Listo | Puntos guardados: {total_points}"
        )
        
    def clear_canvas(self):
        """Clear the canvas"""
        if messagebox.askyesno("Confirmar", "¿Desea limpiar el canvas y borrar todas las trayectorias?"):
            self.canvas.delete("drawing")
            self.coordinates_cm = []
            self.current_path = []
            self.update_status()
            messagebox.showinfo("Éxito", "Canvas limpiado correctamente")
            
    def save_coordinates(self):
        """Save coordinates to JSON file"""
        if not self.coordinates_cm:
            messagebox.showwarning("Advertencia", "No hay coordenadas para guardar")
            return
            
        # Create data structure
        data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "canvas_size_cm": {
                    "width": self.canvas_width_cm,
                    "height": self.canvas_height_cm
                },
                "units": "centimeters",
                "conversion_factor": f"1 cm = {self.CM_TO_PIXELS} pixels"
            },
            "paths": self.coordinates_cm,
            "total_paths": len(self.coordinates_cm),
            "total_points": sum(len(path) for path in self.coordinates_cm)
        }
        
        # Generate filename
        filename = f"coordenadas_scara_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join("/home/runner/work/Robot-scara/Robot-scara", filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            messagebox.showinfo(
                "Éxito",
                f"Coordenadas guardadas correctamente en:\n{filename}\n\n"
                f"Total de trayectorias: {data['total_paths']}\n"
                f"Total de puntos: {data['total_points']}"
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar coordenadas:\n{str(e)}")
            
    def resize_canvas_dialog(self):
        """Show dialog to resize canvas"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajustar Tamaño del Canvas")
        dialog.geometry("400x250")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Title
        title_label = tk.Label(
            dialog,
            text="Configurar Dimensiones del Canvas",
            font=("Helvetica", 12, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        title_label.pack(pady=20)
        
        # Width input
        width_frame = tk.Frame(dialog, bg=self.bg_color)
        width_frame.pack(pady=10)
        
        tk.Label(
            width_frame,
            text="Ancho (cm):",
            font=("Helvetica", 10),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(side=tk.LEFT, padx=5)
        
        width_entry = tk.Entry(width_frame, font=("Helvetica", 10), width=10)
        width_entry.insert(0, str(self.canvas_width_cm))
        width_entry.pack(side=tk.LEFT, padx=5)
        
        # Height input
        height_frame = tk.Frame(dialog, bg=self.bg_color)
        height_frame.pack(pady=10)
        
        tk.Label(
            height_frame,
            text="Alto (cm):",
            font=("Helvetica", 10),
            bg=self.bg_color,
            fg=self.text_color
        ).pack(side=tk.LEFT, padx=5)
        
        height_entry = tk.Entry(height_frame, font=("Helvetica", 10), width=10)
        height_entry.insert(0, str(self.canvas_height_cm))
        height_entry.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        def apply_size():
            try:
                width = float(width_entry.get())
                height = float(height_entry.get())
                
                if width <= 0 or height <= 0:
                    messagebox.showerror("Error", "Las dimensiones deben ser mayores a 0")
                    return
                    
                if width > 200 or height > 200:
                    if not messagebox.askyesno(
                        "Confirmar",
                        f"Las dimensiones son muy grandes ({width}×{height} cm).\n"
                        "¿Desea continuar?"
                    ):
                        return
                        
                self.canvas_width_cm = width
                self.canvas_height_cm = height
                self.update_canvas_size()
                self.canvas.delete("grid")
                self.draw_grid()
                self.settings_label.configure(text=self.get_settings_text())
                messagebox.showinfo("Éxito", f"Canvas redimensionado a {width}×{height} cm")
                dialog.destroy()
                
            except ValueError:
                messagebox.showerror("Error", "Por favor ingrese valores numéricos válidos")
        
        button_frame = tk.Frame(dialog, bg=self.bg_color)
        button_frame.pack(pady=20)
        
        apply_btn = tk.Button(
            button_frame,
            text="Aplicar",
            command=apply_size,
            font=('Helvetica', 10, 'bold'),
            bg=self.button_color,
            fg=self.text_color,
            activebackground=self.accent_color,
            padx=20,
            pady=5
        )
        apply_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            command=dialog.destroy,
            font=('Helvetica', 10, 'bold'),
            bg=self.button_color,
            fg=self.text_color,
            activebackground="#E74C3C",
            padx=20,
            pady=5
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
    def set_line_thickness(self):
        """Set line thickness"""
        thickness = simpledialog.askinteger(
            "Grosor de Línea",
            f"Ingrese el grosor de línea (1-20):\nGrosor actual: {self.line_thickness}px",
            initialvalue=self.line_thickness,
            minvalue=1,
            maxvalue=20
        )
        
        if thickness is not None:
            self.line_thickness = thickness
            self.settings_label.configure(text=self.get_settings_text())
            messagebox.showinfo("Éxito", f"Grosor de línea establecido a {thickness}px")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = ScaraGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
