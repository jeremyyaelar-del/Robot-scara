# Editor de Trazos - Mejoras Implementadas

## Cambios Principales

### 1. Soporte para Entidades DXF Complejas (NUEVO)
- ✅ **SPLINE**: Curvas Bézier/NURBS convertidas a trazos suavizados
- ✅ **ARC**: Arcos convertidos a polilíneas con 20 segmentos
- ✅ **ELLIPSE**: Elipses convertidas a trazos suavizados
- ✅ **POLYLINE**: Soporte completo para polilíneas 3D
- ✅ Manejo robusto de errores con ezdxf.recover
- ✅ Estadísticas detalladas al cargar archivos

**Archivos compatibles:**
```
✓ Diseños arquitectónicos con curvas complejas
✓ Arte vectorial con splines (caligrafía, logos)
✓ Archivos de AutoCAD, LibreCAD, FreeCAD, Inkscape
✓ Archivos DXF corruptos (con recuperación automática)
```

### 2. Formato DXF en lugar de JSON
- ✅ Los archivos ahora se guardan en formato DXF (estándar CNC)
- ✅ Compatible con AutoCAD, LibreCAD, FreeCAD, etc.
- ✅ Unidades en milímetros (estándar para CNC)
- ✅ Formato R2010 para máxima compatibilidad

**Antes:**
```
💾 Guardar JSON  →  archivo.json
📂 Cargar JSON   →  Solo archivos propios
```

**Ahora:**
```
💾 Guardar DXF   →  archivo.dxf (compatible CNC)
📂 Cargar DXF    →  Cualquier archivo DXF externo
```

### 3. Guías de Medición Mejoradas
Las guías ahora tienen:
- ✅ Sistema de coordenadas cartesiano
- ✅ Numeración en centímetros (1, 2, 3...)
- ✅ Ejes X e Y claramente marcados
- ✅ Ejes principales más gruesos

**Visualización:**
```
Y
↑
3 |----+----+----+----+
  |    |    |    |    |
2 |----+----+----+----+
  |    |    |    |    |
1 |----+----+----+----+
  |    |    |    |    |
0 +----+----+----+----+→ X
  0    1    2    3    4
```

### 4. Borrador Mejorado
- ✅ Ahora borra elementos cercanos (no dibuja blanco)
- ✅ Las guías de medición están protegidas
- ✅ Solo afecta trazos y formas dibujadas
- ✅ No puede borrar las líneas de referencia

**Comportamiento:**
- Antes: Dibujaba líneas blancas sobre el dibujo
- Ahora: Elimina elementos bajo el cursor, excepto guías

### 5. Compatibilidad CNC

#### Exportación DXF:
- Capas organizadas: STROKES y SHAPES
- Conversión automática píxeles → milímetros
- Inversión del eje Y (estándar CAD)
- Colores mapeados a AutoCAD Color Index (ACI)

#### Importación DXF:
- Lee archivos de cualquier software CAD
- Convierte LWPOLYLINE, POLYLINE a trazos
- Convierte LINE, CIRCLE a formas
- Convierte SPLINE, ARC, ELLIPSE a trazos suavizados
- Manejo robusto de errores con recuperación automática
- Muestra estadísticas de entidades cargadas
- Permite modificación con herramientas existentes

## Flujo de Trabajo para CNC

### Crear Diseño:
1. Abrir editor_trazos.py
2. Configurar tamaño del canvas en cm
3. Activar guías de medición
4. Dibujar piezas con herramientas
5. Guardar como .dxf

### Usar en CNC:
1. Abrir archivo .dxf en software CNC
2. Verificar unidades (mm)
3. Configurar parámetros de corte
4. Ejecutar en máquina

### Modificar Diseños Externos:
1. Cargar archivo .dxf (de AutoCAD, etc.)
2. Modificar con herramientas del editor
3. Guardar cambios en .dxf
4. Usar en CNC

## Archivos Modificados

### editor_trazos.py
- Importación de ezdxf y numpy
- Nuevas funciones: _save_dxf(), _load_dxf()
- Conversiones de color: _color_to_aci(), _aci_to_color()
- Constante PIXELS_PER_MM para conversión
- Guías mejoradas con numeración
- Borrador con detección de tags

### README.md
- Sección de compatibilidad DXF/CNC
- Instrucciones de instalación de ezdxf
- Ejemplos de uso con CNC
- Lista de software compatible

### GUIA_USO.md
- Workflow para CNC
- Solución de problemas con DXF
- Consejos para uso en CNC
- Sección de formato DXF

### Archivos de Ejemplo
- Eliminado: ejemplo_dibujo.json
- Agregado: ejemplo_dibujo.dxf (con formas de ejemplo)

## Pruebas Realizadas

✅ Exportación DXF con múltiples trazos y formas
✅ Importación DXF desde archivos externos
✅ Conversión píxeles ↔ milímetros
✅ Conversión de colores hex ↔ ACI
✅ Guías de medición con numeración
✅ Borrador respetando guías
✅ Compatibilidad con formato R2010

## Tecnologías Utilizadas

- **ezdxf**: Librería Python para manejo de archivos DXF
- **numpy**: Dependencia de ezdxf para operaciones matemáticas
- **tkinter**: Interfaz gráfica (sin cambios)

## Instalación

```bash
pip install ezdxf
```

Esto instalará automáticamente numpy como dependencia.

## Compatibilidad

### Software CAD/CAM Compatible:
- AutoCAD (todas las versiones modernas)
- LibreCAD
- FreeCAD
- QCAD
- SolidWorks
- Fusion 360
- OnShape
- Inkscape (con plugin DXF)

### Máquinas CNC Compatible:
- Cortadoras láser
- Routers CNC
- Fresadoras CNC
- Plotters de corte
- Grabadores láser

(Cualquier máquina que acepte formato DXF)
