# Robot SCARA - Interfaz de Control

Interfaz gráfica mejorada para el control y visualización de trayectorias de un robot SCARA.

## Características

### 1. **Sistema de Unidades en Centímetros**
- El lienzo trabaja en unidades de centímetros para mayor realismo
- Factor de conversión: **1 cm = 37.8 píxeles**
- Trazos más precisos para entornos físicos

### 2. **Barras de Desplazamiento**
- Barras lateral e inferior para navegar en el lienzo
- Soporte para canvas más grandes que la ventana visible
- Navegación fluida con scroll del mouse

### 3. **Diseño Elegante y Moderno**
- Esquema de colores profesional (azul oscuro y gris)
- Botones estilizados con efectos hover
- Interfaz intuitiva y atractiva

### 4. **Trazos Continuos con Grosor Ajustable**
- Dibujo de líneas continuas en lugar de píxeles individuales
- Grosor ajustable (1-20 píxeles)
- Líneas suaves con capstyle redondo

### 5. **Ajuste Dinámico del Tamaño del Lienzo**
- Diálogo para configurar dimensiones en centímetros
- Validación de entrada con confirmación para tamaños grandes
- Redibujado automático de la cuadrícula

### 6. **Guardado de Coordenadas en Centímetros**
- Exportación automática a formato JSON
- Coordenadas guardadas en centímetros (unidades reales)
- Metadatos completos (timestamp, tamaño del canvas, factor de conversión)

## Instalación

### Requisitos
- Python 3.6 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python)

### Linux/Ubuntu
```bash
# Instalar tkinter si no está disponible
sudo apt-get install python3-tk

# Ejecutar la aplicación
python3 gui_scara.py
```

### Windows
```bash
# Tkinter viene incluido con Python para Windows
python gui_scara.py
```

### macOS
```bash
# Tkinter viene incluido con Python para macOS
python3 gui_scara.py
```

## Uso

### Controles Principales

1. **Limpiar Canvas**: Borra todas las trayectorias dibujadas
2. **Guardar Coordenadas**: Exporta las trayectorias a un archivo JSON con coordenadas en cm
3. **Ajustar Tamaño**: Abre un diálogo para cambiar las dimensiones del canvas en centímetros
4. **Grosor de Línea**: Permite ajustar el grosor del trazo (1-20 píxeles)

### Dibujar Trayectorias

1. Haz clic y arrastra el mouse sobre el canvas para dibujar
2. Las coordenadas se muestran en tiempo real en la barra de estado
3. Cada trazo se guarda automáticamente al soltar el botón del mouse

### Guardar Coordenadas

Las coordenadas se guardan en formato JSON con la siguiente estructura:

```json
{
  "metadata": {
    "timestamp": "2026-01-19T...",
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
      [10.7, 15.3],
      ...
    ]
  ],
  "total_paths": 1,
  "total_points": 150
}
```

## Características Técnicas

- **Grid de Referencia**: Cuadrícula de 1 cm con etiquetas cada 5 cm
- **Conversión Automática**: Todas las coordenadas se convierten automáticamente a cm
- **Scroll Region**: Canvas con región de scroll ajustable
- **Validación de Entrada**: Validación de dimensiones y valores numéricos
- **Gestión de Errores**: Mensajes de error claros y confirmaciones

## Estructura del Proyecto

```
Robot-scara/
├── gui_scara.py          # Aplicación principal
├── requirements.txt      # Dependencias (opcional)
├── README.md            # Este archivo
└── coordenadas_*.json   # Archivos de coordenadas exportadas
```

## Licencia

Este proyecto es de código abierto.
