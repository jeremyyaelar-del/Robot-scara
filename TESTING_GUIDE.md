# Guía de Pruebas - Robot SCARA

## Cómo Probar la Interfaz

### 1. Abrir la Aplicación
1. Abra `index.html` en su navegador web
2. La interfaz debe mostrar:
   - Panel de herramientas fijo a la izquierda
   - Canvas blanco de 100x100 cm en el centro
   - Todos los controles visibles

### 2. Probar Configuración del Canvas
1. Ingrese un nuevo tamaño (ej. 200 cm ancho, 150 cm alto)
2. Haga clic en "Aplicar Tamaño"
3. El canvas debe redimensionarse
4. Si el canvas es más grande que la ventana, deben aparecer scrollbars

### 3. Probar Modo Dibujar
1. Asegúrese de que "Modo Dibujar" esté activo (botón verde)
2. Haga clic y arrastre en el canvas para dibujar
3. Debe aparecer una línea azul con puntos rojos
4. El contador de "Puntos dibujados" debe incrementarse

### 4. Probar Modo Regla
1. Haga clic en "Modo Regla" (el botón debe ponerse verde)
2. Haga clic en un punto del canvas
3. Arrastre hasta otro punto y suelte
4. Debe aparecer una línea roja punteada
5. La "Distancia medida" debe mostrar la distancia en cm

### 5. Probar Guardar Coordenadas
1. Dibuje alguna trayectoria
2. Haga clic en "Guardar Coordenadas"
3. Debe descargarse un archivo JSON con las coordenadas

### 6. Probar Cargar JSON
1. Haga clic en "Cargar JSON"
2. Seleccione uno de los archivos de ejemplo:
   - `trajectory_example.json` (trayectoria simple)
   - `trajectory_circle.json` (trayectoria circular)
3. El canvas debe ajustarse al tamaño especificado
4. La trayectoria debe dibujarse automáticamente

### 7. Probar Scrollbars
1. Configure el canvas a un tamaño grande (ej. 300x300 cm)
2. Haga clic en "Aplicar Tamaño"
3. Deben aparecer scrollbars vertical y horizontal
4. Al desplazar, el panel de herramientas debe permanecer fijo
5. El canvas debe ser completamente accesible

### 8. Probar Limpiar Canvas
1. Con alguna trayectoria dibujada
2. Haga clic en "Limpiar Canvas"
3. Confirme en el diálogo
4. El canvas debe quedar en blanco
5. El contador de puntos debe volver a 0

## Características Implementadas

✅ Edición del tamaño del canvas en centímetros
✅ Barras de desplazamiento horizontal y vertical
✅ Panel de herramientas fijo (siempre visible al desplazar)
✅ Modo dibujar para crear trayectorias
✅ Modo regla para medir distancias
✅ Guardar coordenadas en formato JSON
✅ Cargar trayectorias desde archivos JSON externos
✅ Dos archivos JSON de ejemplo incluidos
✅ Interfaz completamente en español
✅ Diseño responsive y moderno

## Formato JSON

Las coordenadas se guardan en centímetros. Ejemplo:

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

## Navegadores Soportados

- Chrome/Chromium 90+
- Firefox 88+
- Safari 14+
- Edge 90+
