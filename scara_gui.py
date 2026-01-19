#!/usr/bin/env python3
"""
GUI para el control del robot SCARA
Permite trazar líneas en un canvas y guardar las coordenadas
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime


class ScaraGUI:
    """Interfaz gráfica para el control del robot SCARA"""
    
    def __init__(self, root):
        """Inicializa la GUI"""
        self.root = root
        self.root.title("Control Robot SCARA")
        
        # Lista para almacenar las coordenadas
        self.coordinates = []
        
        # Variable para el estado de dibujo
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        
        # Configurar la interfaz
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura los elementos de la interfaz"""
        # Frame principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas para dibujar
        self.canvas = tk.Canvas(
            main_frame,
            width=800,
            height=600,
            bg='white',
            relief=tk.SUNKEN,
            borderwidth=2
        )
        self.canvas.pack(pady=(0, 10))
        
        # Eventos del mouse para dibujar
        self.canvas.bind('<Button-1>', self._start_drawing)
        self.canvas.bind('<B1-Motion>', self._draw)
        self.canvas.bind('<ButtonRelease-1>', self._stop_drawing)
        
        # Frame para los botones
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        # Botón para limpiar el canvas
        clear_button = tk.Button(
            button_frame,
            text="Limpiar Canvas",
            command=self._clear_canvas,
            bg='#ff6b6b',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Botón para guardar coordenadas
        save_button = tk.Button(
            button_frame,
            text="Guardar Coordenadas",
            command=self._save_coordinates,
            bg='#4ecdc4',
            fg='white',
            font=('Arial', 12, 'bold'),
            padx=20,
            pady=10
        )
        save_button.pack(side=tk.LEFT, padx=5)
        
        # Label para mostrar información
        self.info_label = tk.Label(
            main_frame,
            text="Puntos capturados: 0",
            font=('Arial', 10)
        )
        self.info_label.pack(pady=(10, 0))
        
    def _start_drawing(self, event):
        """Inicia el dibujo cuando se presiona el mouse"""
        self.is_drawing = True
        self.last_x = event.x
        self.last_y = event.y
        # Agregar el punto inicial
        self.coordinates.append((event.x, event.y))
        self._update_info_label()
        
    def _draw(self, event):
        """Dibuja líneas mientras se mueve el mouse"""
        if self.is_drawing and self.last_x is not None and self.last_y is not None:
            # Dibujar línea desde el último punto al punto actual
            self.canvas.create_line(
                self.last_x,
                self.last_y,
                event.x,
                event.y,
                fill='blue',
                width=2,
                smooth=True
            )
            # Actualizar la última posición
            self.last_x = event.x
            self.last_y = event.y
            # Agregar el nuevo punto a la lista
            self.coordinates.append((event.x, event.y))
            self._update_info_label()
            
    def _stop_drawing(self, event):
        """Detiene el dibujo cuando se suelta el mouse"""
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        
    def _clear_canvas(self):
        """Limpia el canvas y reinicia las coordenadas"""
        self.canvas.delete('all')
        self.coordinates = []
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        self._update_info_label()
        messagebox.showinfo("Canvas Limpio", "El canvas ha sido limpiado")
        
    def _save_coordinates(self):
        """Guarda las coordenadas en un archivo de texto"""
        if not self.coordinates:
            messagebox.showwarning(
                "Sin Datos",
                "No hay coordenadas para guardar. Dibuja algo primero."
            )
            return
            
        # Generar nombre de archivo por defecto con timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"coordenadas_scara_{timestamp}.txt"
        
        # Mostrar diálogo para guardar archivo
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
            initialfile=default_filename
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    f.write("# Coordenadas del Robot SCARA\n")
                    f.write(f"# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total de puntos: {len(self.coordinates)}\n")
                    f.write("# Formato: x, y\n")
                    f.write("\n")
                    
                    for i, (x, y) in enumerate(self.coordinates):
                        f.write(f"{x}, {y}\n")
                        
                messagebox.showinfo(
                    "Guardado Exitoso",
                    f"Coordenadas guardadas en:\n{filename}\n\nTotal de puntos: {len(self.coordinates)}"
                )
            except Exception as e:
                messagebox.showerror(
                    "Error",
                    f"Error al guardar el archivo:\n{str(e)}"
                )
                
    def _update_info_label(self):
        """Actualiza el label de información"""
        self.info_label.config(text=f"Puntos capturados: {len(self.coordinates)}")


def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = ScaraGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
