# Guía de Uso - Editor de Trazos Interactivo

## Inicio Rápido

### 1. Ejecutar la Aplicación

```bash
python3 editor_trazos.py
```

### 2. Interfaz de Usuario

La aplicación se divide en tres áreas principales:

#### Panel Superior (Herramientas)
- **✏️ Pincel**: Para dibujar trazos libres
- **🗑️ Borrador**: Para borrar partes del dibujo
- **📏 Línea**: Para dibujar líneas rectas
- **⭕ Círculo**: Para dibujar círculos
- **▭ Rectángulo**: Para dibujar rectángulos
- **△ Triángulo**: Para dibujar triángulos

#### Panel Izquierdo (Configuración)

**Grosor del Trazo:**
- Campo de entrada numérica
- Selector de unidades (pixels/cm)
- Control deslizante para ajuste rápido

**Color:**
- Vista previa del color actual
- Botón "Elegir Color" para selector de color

**Tamaño del Lienzo:**
- Ancho y alto en centímetros
- Botón "Aplicar Tamaño" para actualizar
- Checkbox para mostrar/ocultar guías

**Archivo:**
- 💾 Guardar JSON
- 📂 Cargar JSON
- 🗑️ Limpiar Todo

#### Área Central (Canvas)
- Espacio de dibujo principal
- Guías de medición (opcionales)
- Barras de desplazamiento para canvas grandes

## Ejemplos de Uso

### Dibujar un Trazo Libre

1. Seleccione "✏️ Pincel"
2. Ajuste el grosor (ej: 5 pixels)
3. Elija un color
4. Haga clic y arrastre en el canvas

### Dibujar una Forma

1. Seleccione la forma (ej: "⭕ Círculo")
2. Haga clic en el punto inicial
3. Arrastre hasta el tamaño deseado
4. Suelte el botón del mouse

### Configurar el Canvas

1. Ingrese dimensiones (ej: Ancho: 50, Alto: 30)
2. Haga clic en "Aplicar Tamaño"
3. Active "Mostrar Guías de Medición" para ver la cuadrícula

### Guardar su Trabajo

1. Haga clic en "💾 Guardar JSON"
2. Elija ubicación y nombre
3. El archivo guardará todos los trazos y formas

### Cargar un Dibujo

1. Haga clic en "📂 Cargar JSON"
2. Seleccione un archivo `.json`
3. El dibujo se cargará automáticamente

## Atajos y Consejos

### Consejos de Uso
- **Grosor en CM**: Útil para trabajos que requieren medidas reales
- **Guías**: Ayudan a mantener proporciones precisas
- **Scrollbars**: Permiten trabajar con canvas muy grandes
- **Borrador**: Use un grosor grande para borrar áreas amplias

### Buenas Prácticas
1. Guarde frecuentemente su trabajo
2. Use nombres descriptivos para los archivos
3. Active las guías para trabajos de precisión
4. Ajuste el tamaño del canvas antes de empezar a dibujar

## Solución de Problemas

### El canvas no se actualiza
- Haga clic en "Aplicar Tamaño"
- Verifique que los valores sean numéricos

### Error al cargar JSON
- Verifique que el archivo tenga formato JSON válido
- Compruebe que contenga las claves requeridas

### Las guías no aparecen
- Active el checkbox "Mostrar Guías de Medición"
- Asegúrese de que el canvas esté configurado

## Formato del Archivo JSON

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
      "color": "#RRGGBB",
      "width": number
    }
  ],
  "shapes": [
    {
      "type": "circle|rectangle|line|triangle",
      "start": [x1, y1],
      "end": [x2, y2],
      "color": "#RRGGBB",
      "width": number
    }
  ]
}
```

## Requisitos del Sistema

- Python 3.6 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python)
- Sistema operativo: Windows, macOS o Linux

## Soporte

Para reportar problemas o sugerencias, por favor abra un issue en el repositorio de GitHub.
