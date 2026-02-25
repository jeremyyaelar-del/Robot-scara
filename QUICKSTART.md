# Inicio Rápido - Robot SCARA

## 🚀 Comenzar en 30 Segundos

1. **Abrir la aplicación**
   ```
   Abra index.html en su navegador
   ```

2. **Probar el dibujo**
   - El botón "Modo Dibujar" ya está activo (verde)
   - Haga clic y arrastre en el canvas blanco
   - Verá una línea azul con puntos rojos

3. **Probar la regla**
   - Haga clic en "Modo Regla"
   - Haga clic en dos puntos del canvas
   - Verá la distancia en centímetros

4. **Cargar un ejemplo**
   - Haga clic en "Cargar JSON"
   - Seleccione `trajectory_circle.json`
   - Verá un círculo dibujado automáticamente

## 📋 Funciones Principales

### Configurar Canvas
```
1. Ingrese dimensiones en cm (ej. 200 x 150)
2. Clic en "Aplicar Tamaño"
3. El canvas se redimensiona
```

### Dibujar
```
1. Botón "Modo Dibujar" (debe estar verde)
2. Clic y arrastre en el canvas
3. Observe el contador de puntos
```

### Medir
```
1. Botón "Modo Regla"
2. Clic en punto inicial
3. Arrastre hasta punto final
4. Vea la distancia en cm
```

### Guardar
```
1. Dibuje una trayectoria
2. Clic en "Guardar Coordenadas"
3. Se descarga un archivo JSON
```

### Cargar
```
1. Clic en "Cargar JSON"
2. Seleccione archivo .json
3. La trayectoria se dibuja automáticamente
```

## 📁 Archivos de Ejemplo Incluidos

- `trajectory_example.json` - Trayectoria simple (9 puntos)
- `trajectory_circle.json` - Círculo complejo (34 puntos)

## ⚙️ Requisitos

- Navegador moderno (Chrome, Firefox, Safari, Edge)
- Sin instalación necesaria
- Sin dependencias externas

## 🎯 Casos de Uso

**Diseñar nueva trayectoria:**
1. Configurar tamaño del canvas
2. Dibujar con el mouse
3. Guardar como JSON

**Revisar trayectoria existente:**
1. Cargar archivo JSON
2. Usar regla para verificar distancias
3. Modificar si es necesario

**Comparar trayectorias:**
1. Cargar primera trayectoria
2. Medir puntos clave
3. Limpiar canvas
4. Cargar segunda trayectoria
5. Comparar mediciones

## 💡 Consejos

- Use canvas grande (300+ cm) para proyectos complejos
- Las scrollbars aparecen automáticamente
- El panel de herramientas siempre es visible
- Las coordenadas se guardan en centímetros
- Puede cargar sus propios archivos JSON

## ❓ Solución de Problemas

**El canvas es muy pequeño:**
- Aumente el tamaño en los campos de entrada
- Haga clic en "Aplicar Tamaño"

**No puedo ver todo el canvas:**
- Use las scrollbars horizontales/verticales
- El panel de herramientas permanece fijo

**Error al cargar JSON:**
- Verifique que el archivo sea .json válido
- Revise la estructura en los ejemplos incluidos

**La regla no funciona:**
- Asegúrese de que "Modo Regla" esté activo (verde)
- Haga clic, arrastre y suelte

## 📖 Más Información

- Ver `README.md` para documentación completa
- Ver `TESTING_GUIDE.md` para pruebas detalladas
- Ver `IMPLEMENTATION_SUMMARY.md` para detalles técnicos
