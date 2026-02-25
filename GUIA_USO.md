# Guía de Uso - Robot SCARA GUI

## Inicio Rápido

### Ejecutar la Aplicación

```bash
python3 gui_scara.py
```

### Ejecutar el Demo

```bash
python3 demo.py
```

## Funcionalidades Principales

### 1. Dibujar Trayectorias

1. Haz clic en el canvas y mantén presionado el botón del mouse
2. Arrastra para dibujar una trayectoria
3. Suelta el botón para finalizar el trazo
4. Las coordenadas se guardan automáticamente en centímetros

**Ejemplo:**
- Dibuja un cuadrado: Haz 4 trazos consecutivos formando un cuadrado
- Las coordenadas se mostrarán en tiempo real en la barra de estado

### 2. Ajustar el Grosor de Línea

1. Haz clic en el botón **"Grosor de Línea"**
2. Ingresa un valor entre 1 y 20 píxeles
3. Los nuevos trazos usarán el grosor especificado

**Valores recomendados:**
- Líneas finas: 1-3 px
- Líneas normales: 4-6 px
- Líneas gruesas: 7-20 px

### 3. Ajustar el Tamaño del Canvas

1. Haz clic en **"Ajustar Tamaño"**
2. Ingresa las dimensiones en centímetros:
   - Ancho (width)
   - Alto (height)
3. Haz clic en **"Aplicar"**

**Ejemplos de tamaños:**
- Pequeño: 30 × 25 cm
- Mediano: 50 × 40 cm (por defecto)
- Grande: 100 × 80 cm
- Extra grande: 150 × 120 cm

### 4. Limpiar el Canvas

1. Haz clic en **"Limpiar Canvas"**
2. Confirma la acción en el diálogo
3. Todas las trayectorias se borrarán

⚠️ **Advertencia:** Esta acción no se puede deshacer

### 5. Guardar Coordenadas

1. Dibuja una o más trayectorias
2. Haz clic en **"Guardar Coordenadas"**
3. El archivo se guardará automáticamente en el directorio actual

**Nombre del archivo:**
```
coordenadas_scara_YYYYMMDD_HHMMSS.json
```

**Ejemplo:** `coordenadas_scara_20260119_143052.json`

## Formato de Datos Exportados

### Estructura del Archivo JSON

```json
{
  "metadata": {
    "timestamp": "2026-01-19T14:30:52.123456",
    "canvas_size_cm": {
      "width": 50,
      "height": 40
    },
    "units": "centimeters",
    "conversion_factor": "1 cm = 37.8 pixels"
  },
  "paths": [
    [
      [10.5, 15.2],
      [10.7, 15.4],
      [11.0, 15.8]
    ],
    [
      [20.3, 25.1],
      [21.5, 26.3]
    ]
  ],
  "total_paths": 2,
  "total_points": 5
}
```

### Campos del Metadata

- **timestamp**: Fecha y hora de exportación (ISO 8601)
- **canvas_size_cm**: Dimensiones del canvas en centímetros
- **units**: Unidades de las coordenadas (siempre "centimeters")
- **conversion_factor**: Factor de conversión píxel-centímetro

### Estructura de las Coordenadas

Cada trayectoria (path) es una lista de puntos [x, y] en centímetros:

```python
paths = [
    # Primera trayectoria
    [
        [x1, y1],  # Primer punto
        [x2, y2],  # Segundo punto
        ...
    ],
    # Segunda trayectoria
    [
        [x1, y1],
        [x2, y2],
        ...
    ]
]
```

## Usar las Coordenadas en Python

### Cargar Coordenadas

```python
import json

# Cargar archivo
with open('coordenadas_scara_20260119_143052.json', 'r') as f:
    data = json.load(f)

# Acceder a las coordenadas
paths = data['paths']
total_paths = data['total_paths']
total_points = data['total_points']

# Procesar cada trayectoria
for i, path in enumerate(paths):
    print(f"Trayectoria {i+1}: {len(path)} puntos")
    for x, y in path:
        print(f"  Punto: ({x} cm, {y} cm)")
```

### Convertir a Otras Unidades

```python
# Convertir de cm a mm
def cm_to_mm(coords):
    return [[x * 10, y * 10] for x, y in coords]

# Convertir de cm a pulgadas
def cm_to_inches(coords):
    return [[x / 2.54, y / 2.54] for x, y in coords]

# Uso
path_mm = cm_to_mm(paths[0])
path_inches = cm_to_inches(paths[0])
```

## Navegación con Scrollbars

### Cuando usar los Scrollbars

Los scrollbars aparecen automáticamente cuando:
- El canvas es más grande que el área visible
- Has configurado dimensiones grandes (ej: 100 × 80 cm o más)

### Cómo Navegar

1. **Scrollbar Vertical (derecha):**
   - Arrastra para mover arriba/abajo
   - Usa la rueda del mouse

2. **Scrollbar Horizontal (inferior):**
   - Arrastra para mover izquierda/derecha
   - Usa Shift + rueda del mouse (en algunos sistemas)

## Atajos de Teclado

Actualmente no hay atajos de teclado implementados. Todas las funciones se acceden mediante botones.

## Resolución de Problemas

### El canvas aparece vacío
- Verifica que las dimensiones no sean demasiado grandes
- Intenta reducir el tamaño a 50 × 40 cm

### Las líneas no se dibujan
- Asegúrate de mantener presionado el botón del mouse
- Verifica que el grosor de línea no sea 0

### No se puede guardar
- Verifica que tengas permisos de escritura en el directorio
- Asegúrate de haber dibujado al menos una trayectoria

### La aplicación no inicia
- Verifica que Python 3.6+ esté instalado
- Instala tkinter: `sudo apt-get install python3-tk` (Linux)

## Consejos y Trucos

### Para Trazos Precisos
1. Usa un grosor de línea pequeño (1-2 px)
2. Configura un canvas grande (100+ cm)
3. Usa los scrollbars para acercarte a la zona de trabajo

### Para Visualización Rápida
1. Usa un canvas pequeño (30 × 25 cm)
2. Grosor de línea mayor (5-8 px)
3. Dibuja trayectorias simples

### Para Documentación
1. Dibuja todas las trayectorias necesarias
2. Guarda con un nombre descriptivo
3. Incluye metadata en tus notas

## Preguntas Frecuentes

**P: ¿Puedo cambiar el factor de conversión?**
R: Sí, modifica `CM_TO_PIXELS` en `gui_scara.py`

**P: ¿Se pueden importar coordenadas?**
R: Actualmente no, solo exportación. Esta característica puede añadirse en el futuro.

**P: ¿Hay límite de trayectorias?**
R: No hay límite, pero muchas trayectorias pueden hacer lenta la aplicación.

**P: ¿Se puede deshacer un trazo?**
R: No actualmente. Usa "Limpiar Canvas" para empezar de nuevo.

**P: ¿Funciona en Windows/Mac?**
R: Sí, Tkinter es multiplataforma. La aplicación funciona en Windows, macOS y Linux.

## Soporte

Para reportar problemas o sugerir mejoras, abre un issue en el repositorio de GitHub.
