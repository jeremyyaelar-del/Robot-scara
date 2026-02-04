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
- 💾 Guardar DXF
- 📂 Cargar DXF
- 🗑️ Limpiar Todo

#### Área Central (Canvas)
- Espacio de dibujo principal
- Guías de medición con numeración cartesiana (opcionales)
- Ejes X e Y claramente marcados
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

### Usar el Borrador

1. Seleccione "🗑️ Borrador"
2. Ajuste el tamaño del borrador
3. Arrastre sobre las áreas que desea borrar
4. **Nota**: Las guías de medición no se borrarán

### Configurar el Canvas

1. Ingrese dimensiones (ej: Ancho: 50, Alto: 30)
2. Haga clic en "Aplicar Tamaño"
3. Active "Mostrar Guías de Medición" para ver la cuadrícula numerada

### Guardar su Trabajo para CNC

1. Haga clic en "💾 Guardar DXF"
2. Elija ubicación y nombre (ej: `pieza.dxf`)
3. El archivo guardará todos los trazos y formas en formato CNC

### Cargar un Dibujo DXF

1. Haga clic en "📂 Cargar DXF"
2. Seleccione un archivo `.dxf` (puede ser de AutoCAD, LibreCAD, etc.)
3. El dibujo se cargará automáticamente

## Atajos y Consejos

### Consejos de Uso
- **Grosor en CM**: Útil para trabajos que requieren medidas reales
- **Guías numeradas**: Sistema cartesiano facilita mediciones precisas
- **Scrollbars**: Permiten trabajar con canvas muy grandes
- **Borrador mejorado**: Borra solo trazos, no las guías de referencia
- **Formato DXF**: Compatible con la mayoría de software CNC y CAD

### Buenas Prácticas
1. Guarde frecuentemente su trabajo en formato DXF
2. Use nombres descriptivos para los archivos (ej: `pieza_corte_laser.dxf`)
3. Active las guías para trabajos de precisión
4. Ajuste el tamaño del canvas antes de empezar a dibujar
5. Verifique las unidades (mm) antes de enviar a CNC

### Para Uso en CNC
1. Diseñe su pieza con las dimensiones reales en cm
2. Guarde como DXF (las unidades se convierten automáticamente a mm)
3. Importe el archivo en su software CNC (Mach3, LinuxCNC, etc.)
4. Verifique la escala (debe estar en mm)
5. Configure parámetros de corte según su material

## Solución de Problemas

### El canvas no se actualiza
- Haga clic en "Aplicar Tamaño"
- Verifique que los valores sean numéricos

### Error al cargar DXF
- Verifique que el archivo sea DXF válido
- Asegúrese de que sea formato R2010 o compatible
- Algunos archivos DXF muy complejos pueden tardar en cargar

### Las guías no aparecen
- Active el checkbox "Mostrar Guías de Medición"
- Asegúrese de que el canvas esté configurado

### El borrador borra las guías
- Este problema ha sido corregido en la versión actual
- Las guías están protegidas contra el borrador

### Problemas con CNC
- Verifique que las unidades en su CNC estén en mm
- Algunos software CNC requieren invertir el eje Y
- El archivo DXF ya invierte Y automáticamente (estándar CAD)

## Formato del Archivo DXF

El archivo DXF generado incluye:

**Estructura:**
- Formato: AutoCAD R2010
- Unidades: Milímetros (mm)
- Capas: STROKES y SHAPES

**Entidades:**
- LWPOLYLINE: Para trazos libres y polígonos
- LINE: Para líneas rectas
- CIRCLE: Para círculos
- Colores: AutoCAD Color Index (ACI)

**Compatibilidad:**
- Máquinas CNC que aceptan DXF
- AutoCAD, LibreCAD, FreeCAD
- Software CAM (Fusion 360, OnShape, etc.)
- Cortadoras láser y routers CNC

## Requisitos del Sistema

- Python 3.6 o superior
- Tkinter (incluido en la mayoría de instalaciones de Python)
- ezdxf (para archivos DXF)
- numpy (dependencia de ezdxf)
- Sistema operativo: Windows, macOS o Linux

## Soporte

Para reportar problemas o sugerencias, por favor abra un issue en el repositorio de GitHub.
