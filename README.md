# Robot SCARA - GUI Avanzada de Dibujo

Interfaz gráfica avanzada para el control y programación de trayectorias del robot SCARA mediante dibujo.

## Características

### 1. Modos de Dibujo

La GUI ofrece dos modos principales de dibujo:

- **Modo 1 - Mano Alzada**: Permite trazar líneas libremente con el cursor del mouse
- **Modo 2 - Formas Geométricas**: Habilita la creación de trazados precisos usando:
  - Líneas rectas
  - Rectángulos
  - Círculos

### 2. Compatibilidad con Archivos JSON

La aplicación puede cargar archivos de trazados en formato JSON. Se incluyen tres archivos de ejemplo:

- `example_path_points.json` - Trazado basado en puntos conectados (estrella)
- `example_path_lines.json` - Trazado con líneas individuales (cuadrado con diagonales)
- `example_path_complex.json` - Trazado complejo con múltiples paths

**Formato JSON soportado:**

```json
{
  "points": [
    {"x": 100, "y": 200},
    {"x": 150, "y": 100}
  ]
}
```

o

```json
{
  "lines": [
    {"x1": 50, "y1": 50, "x2": 150, "y2": 50}
  ]
}
```

### 3. Ajuste del Grosor de Línea

Los usuarios pueden ajustar el grosor de las líneas trazadas con las siguientes opciones:

- **Píxeles (px)**: Para trabajar directamente en unidades de pantalla
- **Milímetros (mm)**: Para dimensiones reales del robot (conversión automática)

### 4. Función de Zoom

Navegación del canvas mediante atajos de teclado:

- **Control +**: Acercar (zoom in)
- **Control -**: Alejar (zoom out)

## Requisitos

- Python 3.6 o superior
- tkinter (incluido en la mayoría de instalaciones de Python)

## Uso

Para ejecutar la aplicación:

```bash
python robot_gui.py
```

o

```bash
python3 robot_gui.py
```

## Instrucciones de Uso

1. **Seleccionar modo de dibujo**: Usar los botones de radio en la parte superior
2. **Ajustar grosor**: Modificar el valor y seleccionar la unidad (px o mm)
3. **Dibujar**: Hacer clic y arrastrar en el canvas blanco
4. **Cargar archivo**: Usar el botón "Cargar Archivo JSON" para importar trazados
5. **Zoom**: Usar Ctrl + / Ctrl - para acercar o alejar
6. **Limpiar**: Usar el botón "Limpiar Canvas" para borrar todo

## Estructura del Proyecto

```
Robot-scara/
├── robot_gui.py                    # Aplicación principal
├── example_path_points.json        # Ejemplo: trazado con puntos
├── example_path_lines.json         # Ejemplo: trazado con líneas
├── example_path_complex.json       # Ejemplo: trazado complejo
└── README.md                        # Este archivo
```
