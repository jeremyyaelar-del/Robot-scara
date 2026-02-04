# Robot-scara - Editor de Trazos Interactivo para CNC

Aplicación profesional de edición de trazos con características avanzadas usando Python y Tkinter. Optimizada para generar archivos DXF compatibles con máquinas CNC.

## Características

### 1. Canvas Editable
- **Trazos con el mouse**: Dibuje libremente con el mouse y almacene coordenadas
- **Guardar trazos**: Exporte todos los trazos a archivos `.dxf` compatibles con CNC
- **Importar trazos**: Cargue archivos `.dxf` externos (de AutoCAD, LibreCAD, etc.) y visualícelos
- **Modificación**: Edite archivos DXF cargados con las herramientas de dibujo

### 2. Herramientas de Edición
- **Pincel**: Dibuje trazos libres con color y grosor personalizables
- **Borrador**: Borre partes del dibujo (sin afectar las guías de referencia)
- **Línea**: Dibuje líneas rectas
- **Círculo**: Dibuje círculos perfectos
- **Rectángulo**: Dibuje rectángulos
- **Triángulo**: Dibuje triángulos isósceles
- **Selector de grosor**: Configure en píxeles o centímetros
- **Selector de color**: Elija cualquier color para dibujar

### 3. Configuración del Lienzo
- **Tamaño ajustable**: Configure el tamaño del canvas en centímetros
- **Guías de medición mejoradas**: Sistema de coordenadas cartesiano con numeración en cm
- **Ejes principales**: Ejes X e Y claramente marcados
- **Barras de desplazamiento**: Navegue por canvas grandes (horizontal y vertical)
- **Guías protegidas**: Las líneas de referencia no se borran con el borrador

### 4. Compatibilidad con DXF (CNC)
- **Exportar**: Guarde diseños en formato DXF estándar para CNC
- **Importar**: Cargue archivos DXF externos de cualquier software CAD
- **Unidades**: Milímetros (estándar CNC)
- **Formato**: DXF R2010 (máxima compatibilidad)
- **Capas**: Organización automática en capas STROKES y SHAPES
- **Conversión precisa**: Conversión automática píxeles ↔ milímetros

### 5. Interfaz Profesional
- **Diseño azulado**: Tema profesional con tonos azules
- **Responsive**: Se adapta al redimensionar la ventana
- **Intuitivo**: Controles claramente etiquetados y organizados

## Requisitos

- Python 3.6 o superior
- Tkinter (incluido con la mayoría de distribuciones de Python)
- ezdxf (para manejo de archivos DXF)
- numpy (dependencia de ezdxf)

## Instalación

1. Clone el repositorio:
```bash
git clone https://github.com/jeremyyaelar-del/Robot-scara.git
cd Robot-scara
```

2. Instale las dependencias:
```bash
pip install ezdxf
```

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
1. **Guardar**: Haga clic en "💾 Guardar DXF" y elija una ubicación
2. **Cargar**: Haga clic en "📂 Cargar DXF" y seleccione un archivo
3. **Limpiar**: Haga clic en "🗑️ Limpiar Todo" para borrar el canvas

### Usar con CNC
1. Diseñe su pieza en el editor
2. Guarde como archivo DXF
3. Importe el archivo DXF en el software de su CNC
4. Las unidades están en milímetros (estándar CNC)
5. Ajuste parámetros de corte según su máquina

## Formato DXF

Los archivos DXF generados incluyen:

- **Formato**: AutoCAD R2010 (compatible con la mayoría de software CAD/CAM)
- **Unidades**: Milímetros (mm)
- **Capas**:
  - `STROKES`: Trazos libres (LWPOLYLINE)
  - `SHAPES`: Formas geométricas (LINE, CIRCLE, etc.)
- **Entidades soportadas**:
  - LWPOLYLINE (trazos y polígonos)
  - POLYLINE (polilíneas con vértices 3D)
  - LINE (líneas rectas)
  - CIRCLE (círculos)
  - SPLINE (curvas Bézier/NURBS) - convertidas a polilíneas
  - ARC (arcos) - convertidos a polilíneas
  - ELLIPSE (elipses) - convertidas a polilíneas
  - Colores ACI (AutoCAD Color Index)

### Compatibilidad
El formato DXF generado es compatible con:
- Máquinas CNC que aceptan formato DXF
- AutoCAD
- LibreCAD
- FreeCAD
- SolidWorks
- QCAD
- Y la mayoría de software CAD/CAM

## Conversión de Unidades

La aplicación utiliza la siguiente conversión:
- **Pantalla**: 96 DPI estándar
- **Píxeles por cm**: 37.795 px/cm
- **Píxeles por mm**: 3.7795 px/mm
- **DXF**: Coordenadas en milímetros con eje Y invertido (estándar CAD)

## Licencia

Este proyecto está disponible como código abierto.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abra un issue o pull request para sugerencias y mejoras.
