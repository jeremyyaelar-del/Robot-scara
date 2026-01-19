# Robot-scara - Editor de Trazos Interactivo

Aplicación profesional de edición de trazos con características avanzadas usando Python y Tkinter.

## Características

### 1. Canvas Editable
- **Trazos con el mouse**: Dibuje libremente con el mouse y almacene coordenadas
- **Guardar trazos**: Exporte todos los trazos a archivos `.json`
- **Importar trazos**: Cargue archivos `.json` existentes y visualícelos

### 2. Herramientas de Edición
- **Pincel**: Dibuje trazos libres con color y grosor personalizables
- **Borrador**: Borre partes del dibujo con tamaño ajustable
- **Línea**: Dibuje líneas rectas
- **Círculo**: Dibuje círculos perfectos
- **Rectángulo**: Dibuje rectángulos
- **Triángulo**: Dibuje triángulos isósceles
- **Selector de grosor**: Configure en píxeles o centímetros
- **Selector de color**: Elija cualquier color para dibujar

### 3. Configuración del Lienzo
- **Tamaño ajustable**: Configure el tamaño del canvas en centímetros
- **Guías de medición**: Visualice una cuadrícula de 1cm para precisión
- **Barras de desplazamiento**: Navegue por canvas grandes (horizontal y vertical)

### 4. Compatibilidad con JSON
- **Exportar**: Guarde trazos, formas y configuración del canvas
- **Importar**: Cargue archivos JSON con todos los datos
- **Formato completo**: Incluye coordenadas, colores, grosores y tipos de trazo

### 5. Interfaz Profesional
- **Diseño azulado**: Tema profesional con tonos azules
- **Responsive**: Se adapta al redimensionar la ventana
- **Intuitivo**: Controles claramente etiquetados y organizados

## Requisitos

- Python 3.6 o superior
- Tkinter (incluido con la mayoría de distribuciones de Python)

## Instalación

1. Clone el repositorio:
```bash
git clone https://github.com/jeremyyaelar-del/Robot-scara.git
cd Robot-scara
```

2. No se requieren dependencias adicionales (Tkinter viene con Python)

## Uso

Ejecute la aplicación:

```bash
python editor_trazos.py
```

O con Python 3 explícitamente:

```bash
python3 editor_trazos.py
```

También puede hacer el archivo ejecutable (en Linux/Mac):

```bash
chmod +x editor_trazos.py
./editor_trazos.py
```

## Instrucciones de Uso

### Dibujar
1. Seleccione una herramienta (Pincel, Línea, Círculo, etc.)
2. Configure el grosor y color deseados
3. Haga clic y arrastre en el canvas para dibujar

### Configurar el Canvas
1. Ingrese el ancho y alto deseados en centímetros
2. Haga clic en "Aplicar Tamaño"
3. Active/desactive las guías de medición según necesite

### Guardar y Cargar
1. **Guardar**: Haga clic en "💾 Guardar JSON" y elija una ubicación
2. **Cargar**: Haga clic en "📂 Cargar JSON" y seleccione un archivo
3. **Limpiar**: Haga clic en "🗑️ Limpiar Todo" para borrar el canvas

## Formato JSON

Los archivos guardados tienen el siguiente formato:

```json
{
  "canvas_size": {
    "width_cm": 30,
    "height_cm": 20
  },
  "strokes": [
    {
      "type": "brush",
      "points": [[x1, y1], [x2, y2], ...],
      "color": "#000000",
      "width": 2
    }
  ],
  "shapes": [
    {
      "type": "circle",
      "start": [x1, y1],
      "end": [x2, y2],
      "color": "#000000",
      "width": 2
    }
  ]
}
```

## Conversión de Unidades

La aplicación utiliza una conversión aproximada de **37.795 píxeles por centímetro**, basada en la densidad de pantalla estándar de 96 DPI.

## Licencia

Este proyecto está disponible como código abierto.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abra un issue o pull request para sugerencias y mejoras.
