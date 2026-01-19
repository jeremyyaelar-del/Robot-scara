# Guía de Uso de la GUI Avanzada

## Descripción General

La GUI avanzada para el Robot SCARA proporciona una interfaz completa para diseñar trayectorias mediante dibujo. Esta guía explica cómo utilizar todas las funcionalidades implementadas.

## Interfaz de Usuario

```
┌─────────────────────────────────────────────────────────────────────┐
│ Robot SCARA - GUI Avanzada de Dibujo                                │
├─────────────────────────────────────────────────────────────────────┤
│ ╔═══════════════════════════════════════════════════════════════╗ │
│ ║ Controles                                                     ║ │
│ ╠═══════════════════════════════════════════════════════════════╣ │
│ ║ Modo de Dibujo:                                               ║ │
│ ║  ( ) Mano Alzada  (•) Línea Recta  ( ) Rectángulo  ( ) Círculo ║ │
│ ║                                                               ║ │
│ ║ Grosor: [2.0▼]  (•) píxeles (px)  ( ) milímetros (mm)       ║ │
│ ║                                                               ║ │
│ ║ [Cargar Archivo JSON]  [Limpiar Canvas]                      ║ │
│ ║                                                               ║ │
│ ║ Zoom: 100%  (Ctrl + para acercar, Ctrl - para alejar)        ║ │
│ ╚═══════════════════════════════════════════════════════════════╝ │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │                                                             │   │
│ │                    CANVAS DE DIBUJO                         │   │
│ │                      (800 x 600)                            │   │
│ │                                                             │   │
│ │                                                             │   │
│ │                                                             │   │
│ │                                                             │   │
│ │                                                             │   │
│ └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│ ┌─────────────────────────────────────────────────────────────┐   │
│ │ Listo                                                       │   │
│ └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

## Funcionalidades Implementadas

### 1. Modos de Dibujo

#### Modo Mano Alzada
- Seleccionar el botón "Mano Alzada"
- Hacer clic y arrastrar en el canvas para dibujar libremente
- El trazado sigue el movimiento del mouse
- Ideal para dibujos orgánicos o trazados complejos

#### Modo Línea Recta
- Seleccionar el botón "Línea Recta"
- Hacer clic en el punto inicial
- Arrastrar hasta el punto final
- Soltar para crear la línea
- Vista previa en tiempo real durante el arrastre

#### Modo Rectángulo
- Seleccionar el botón "Rectángulo"
- Hacer clic en una esquina
- Arrastrar hasta la esquina opuesta
- Soltar para crear el rectángulo
- Vista previa en tiempo real durante el arrastre

#### Modo Círculo
- Seleccionar el botón "Círculo"
- Hacer clic en el centro
- Arrastrar para definir el radio
- Soltar para crear el círculo
- Vista previa en tiempo real durante el arrastre

### 2. Ajuste del Grosor de Línea

**Opciones:**
- **Píxeles (px)**: Grosor directo en pantalla
  - Útil para diseño visual
  - Valores típicos: 1-10 px
  
- **Milímetros (mm)**: Dimensiones reales del robot
  - Conversión automática a píxeles (1 mm ≈ 3.78 px @ 96 DPI)
  - Útil para precisión mecánica
  - Valores típicos: 0.5-5 mm

**Cómo usar:**
1. Ingresar el valor deseado en el campo "Grosor"
2. Seleccionar la unidad (px o mm)
3. El cambio se aplica automáticamente a nuevos trazos

### 3. Carga de Archivos JSON

**Formatos soportados:**

#### Formato 1: Puntos Conectados
```json
{
  "description": "Descripción del trazado",
  "points": [
    {"x": 100, "y": 200},
    {"x": 150, "y": 100},
    {"x": 200, "y": 200}
  ]
}
```

#### Formato 2: Líneas Individuales
```json
{
  "description": "Descripción del trazado",
  "lines": [
    {"x1": 50, "y1": 50, "x2": 150, "y2": 50},
    {"x1": 150, "y1": 50, "x2": 150, "y2": 150}
  ]
}
```

#### Formato 3: Múltiples Paths
```json
{
  "description": "Descripción del trazado",
  "paths": [
    {
      "name": "Path 1",
      "points": [
        {"x": 250, "y": 100},
        {"x": 200, "y": 180}
      ]
    }
  ]
}
```

**Archivos de Ejemplo Incluidos:**
1. `example_path_points.json` - Estrella de 6 puntos
2. `example_path_lines.json` - Cuadrado con diagonales
3. `example_path_complex.json` - Triángulo y círculo aproximado

**Cómo cargar:**
1. Hacer clic en "Cargar Archivo JSON"
2. Seleccionar el archivo deseado
3. El trazado aparecerá en azul en el canvas
4. Se puede combinar con trazos manuales

### 4. Función de Zoom

**Atajos de teclado:**
- **Ctrl + +**: Acercar (zoom in)
- **Ctrl + -**: Alejar (zoom out)

**Características:**
- Rango de zoom: 10% a 500%
- Incremento/decremento: 20% por paso
- Todos los elementos se escalan proporcionalmente
- El grosor de línea se mantiene visualmente consistente
- Indicador de zoom en la barra de controles

**Uso típico:**
1. Dibujar el trazado general con zoom 100%
2. Usar Ctrl + para acercar a detalles
3. Refinar trazados con precisión
4. Usar Ctrl - para ver el conjunto completo

### 5. Limpiar Canvas

- Botón "Limpiar Canvas" elimina todos los trazos
- Incluye trazos manuales y archivos cargados
- Irreversible - usar con precaución

## Flujo de Trabajo Recomendado

### Caso 1: Diseño desde Cero
1. Seleccionar modo de dibujo apropiado
2. Ajustar grosor de línea
3. Dibujar trazado base
4. Usar zoom para refinar detalles
5. Guardar/exportar (función futura)

### Caso 2: Modificación de Trazado Existente
1. Cargar archivo JSON
2. Seleccionar modo de dibujo
3. Añadir trazos adicionales
4. Ajustar con zoom según necesidad
5. Guardar/exportar (función futura)

### Caso 3: Trazados Precisos
1. Usar modo "Línea Recta" o formas geométricas
2. Ajustar grosor en mm para precisión real
3. Usar zoom para verificar exactitud
4. Combinar múltiples formas

## Ejemplos de Uso

### Dibujar un Logo Simple
```
1. Modo: Rectángulo, Grosor: 2 px
2. Dibujar marco exterior
3. Modo: Círculo, Grosor: 3 px
4. Dibujar elemento central
5. Modo: Mano Alzada, Grosor: 1 px
6. Añadir detalles decorativos
```

### Crear Trayectoria de Ensamblaje
```
1. Cargar: example_path_points.json (trazado base)
2. Modo: Línea Recta, Grosor: 1.5 mm
3. Añadir líneas de conexión
4. Zoom: 200% para precisión
5. Verificar intersecciones
```

### Trazado Artístico
```
1. Modo: Mano Alzada, Grosor: 3 px
2. Dibujar contorno general
3. Grosor: 1 px
4. Añadir detalles finos
5. Modo: Círculo para elementos circulares
```

## Limitaciones Conocidas

1. **Sin deshacer (Undo)**: Usar "Limpiar Canvas" para empezar de nuevo
2. **Sin guardar**: Actualmente no guarda el trabajo (función futura)
3. **Sin capas**: Todos los elementos están en una sola capa
4. **Sin colores**: Todas las líneas son negras (cargadas en azul)

## Extensiones Futuras

- Sistema de deshacer/rehacer
- Guardar trazados en JSON
- Exportar a diferentes formatos
- Selección y edición de elementos individuales
- Paleta de colores
- Sistema de capas
- Mediciones y dimensiones en pantalla
- Integración con control del robot SCARA

## Solución de Problemas

**La aplicación no inicia:**
- Verificar que Python 3.6+ esté instalado
- Verificar que tkinter esté disponible: `python3 -c "import tkinter"`
- Instalar tkinter si es necesario: `sudo apt-get install python3-tk` (Linux)

**No se puede cargar archivo JSON:**
- Verificar que el formato JSON sea válido
- Verificar que contenga "points", "lines" o "paths"
- Ver archivos de ejemplo para referencia

**El zoom no funciona:**
- Verificar que se use la combinación correcta: Ctrl + tecla
- En algunos sistemas puede ser Cmd en lugar de Ctrl (Mac)

**Líneas muy gruesas o muy finas:**
- Verificar la unidad seleccionada (px vs mm)
- Ajustar el valor de grosor
- La conversión mm→px usa 1 mm = 3.78 px (96 DPI)

## Información Técnica

**Tecnologías utilizadas:**
- Python 3
- tkinter (GUI toolkit estándar)
- JSON (formato de datos)

**Resolución del canvas:**
- 800 x 600 píxeles (configurable en código)

**Conversión de unidades:**
- 1 mm = 3.78 px (basado en 96 DPI)
- Ajustable según calibración del sistema

**Coordenadas:**
- Origen (0,0) en esquina superior izquierda
- X aumenta hacia la derecha
- Y aumenta hacia abajo
