# Robot SCARA - Interfaz de Trayectorias

Interfaz web para diseñar y gestionar trayectorias del Robot SCARA.

## Características

### Configuración del Canvas
- **Tamaño personalizable**: Edite el tamaño del canvas en centímetros (ancho y alto)
- **Barras de desplazamiento**: El canvas puede ser más grande que la ventana, con scrollbars horizontal y vertical
- **Panel de herramientas fijo**: Las herramientas permanecen visibles al desplazar el canvas

### Herramientas de Dibujo
- **Modo Dibujar**: Dibuje trayectorias libremente en el canvas haciendo clic y arrastrando
- **Modo Regla**: Mida distancias entre dos puntos (similar a PowerPoint)
- **Limpiar Canvas**: Borre todas las trayectorias dibujadas

### Gestión de Trayectorias
- **Guardar Coordenadas**: Exporte las coordenadas de la trayectoria en formato JSON
- **Cargar JSON**: Importe trayectorias desde archivos JSON externos

## Uso

1. Abra `index.html` en un navegador web moderno
2. Configure el tamaño del canvas según sus necesidades
3. Seleccione el modo de dibujo o regla
4. Dibuje trayectorias haciendo clic y arrastrando en el canvas
5. Guarde las coordenadas o cargue trayectorias existentes

## Archivos de Ejemplo

Se incluyen dos archivos JSON de ejemplo:
- `trajectory_example.json`: Trayectoria lineal simple
- `trajectory_circle.json`: Trayectoria circular compleja

## Formato JSON

```json
{
  "canvasSize": {
    "width": 100,
    "height": 100
  },
  "trajectory": [
    { "x": "10.00", "y": "10.00" },
    { "x": "20.00", "y": "15.00" }
  ],
  "metadata": {
    "pointCount": 2,
    "createdAt": "2026-01-19T22:00:00.000Z",
    "description": "Descripción opcional"
  }
}
```

## Tecnologías

- HTML5 Canvas
- CSS3
- JavaScript (Vanilla)

## Compatibilidad

Funciona en todos los navegadores modernos que soporten HTML5 Canvas.
