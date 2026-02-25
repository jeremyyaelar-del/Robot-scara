# GUI para Control del Robot SCARA

Esta aplicación proporciona una interfaz gráfica básica para el control del robot SCARA, permitiendo a los usuarios trazar trayectorias y guardar las coordenadas.

## Características

- **Canvas interactivo**: Dibuja trayectorias con el cursor del mouse
- **Visualización en tiempo real**: Las líneas se muestran mientras dibujas
- **Contador de puntos**: Muestra el número de puntos capturados
- **Limpiar canvas**: Botón para reiniciar el dibujo
- **Guardar coordenadas**: Exporta las coordenadas a un archivo de texto

## Requisitos

- Python 3.x
- Tkinter (incluido con Python en la mayoría de las instalaciones)

### Instalación de Tkinter (si es necesario)

#### Ubuntu/Debian:
```bash
sudo apt-get install python3-tk
```

#### macOS:
Tkinter viene preinstalado con Python.

#### Windows:
Tkinter viene preinstalado con Python.

## Uso

### Ejecutar la aplicación

```bash
python3 scara_gui.py
```

### Cómo usar la interfaz

1. **Dibujar trayectorias**:
   - Haz clic y mantén presionado el botón izquierdo del mouse
   - Mueve el cursor para dibujar líneas
   - Suelta el botón para terminar el trazo actual
   - Repite para crear múltiples trayectorias

2. **Limpiar el canvas**:
   - Haz clic en el botón "Limpiar Canvas" (rojo)
   - Esto borrará todas las líneas y reiniciará el contador de puntos

3. **Guardar coordenadas**:
   - Haz clic en el botón "Guardar Coordenadas" (azul-verde)
   - Selecciona la ubicación y nombre del archivo
   - El archivo se guardará en formato de texto con las coordenadas (x, y)

## Formato del archivo de coordenadas

El archivo de salida contiene:
- Comentarios con información sobre la fecha y número de puntos
- Cada línea con un par de coordenadas en formato: `x, y`

Ejemplo:
```
# Coordenadas del Robot SCARA
# Generado: 2026-01-19 20:30:00
# Total de puntos: 150
# Formato: x, y

100, 200
102, 205
105, 210
...
```

## Ejecutar pruebas

```bash
python3 test_scara_gui.py
```

## Estructura del proyecto

```
Robot-scara/
├── scara_gui.py         # Aplicación principal de la GUI
├── test_scara_gui.py    # Pruebas unitarias
├── GUI_README.md        # Esta documentación
└── README.md            # README principal del proyecto
```

## Desarrollo futuro

Esta interfaz es la base para desarrollar funcionalidades más avanzadas:
- Conversión de coordenadas del canvas a coordenadas del robot
- Cinemática inversa para el robot SCARA
- Control en tiempo real del robot
- Simulación del movimiento del robot
- Carga de trayectorias desde archivos

## Licencia

Este proyecto es parte del desarrollo del Robot SCARA.
