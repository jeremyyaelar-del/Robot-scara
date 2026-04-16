# Robot SCARA – Sistema de Captura de Trayectorias 2D

Sistema completo de captura de trayectorias para un robot SCARA de 2 articulaciones. Utiliza encoders rotatorios para registrar posiciones exactas y exportar las figuras trazadas a formato DXF.

---

## Estructura del Proyecto

```
arduino/
  robot_scara_encoder.ino   ← Firmware para Arduino (lectura encoders + cinemática)

python/
  scara_visualizer.py       ← Visualizador en tiempo real + exportación DXF
  requirements.txt          ← Dependencias Python

README.md
```

---

## Hardware

| Componente | Descripción |
|---|---|
| Robot | Brazo SCARA con 2 articulaciones rotatorias |
| Encoder | E38S6G5-600B-G24N – 600 PPR, cuadratura 4× = **2400 cuentas/rev** |
| Controlador | Arduino Mega 2560 (recomendado) o Uno/Nano |

---

## Diagrama de Conexiones

```
Arduino Mega 2560
┌──────────────────────────────────────┐
│                                      │
│  PIN 2  ◄──── Encoder 1 – Canal A   │  (Articulación 1)
│  PIN 3  ◄──── Encoder 1 – Canal B   │
│  PIN 4  ◄──── Encoder 1 – Canal Z   │  (señal de home, opcional)
│                                      │
│  PIN 18 ◄──── Encoder 2 – Canal A   │  (Articulación 2)
│  PIN 19 ◄──── Encoder 2 – Canal B   │
│  PIN 5  ◄──── Encoder 2 – Canal Z   │  (señal de home, opcional)
│                                      │
│  PIN 13 ────► LED de estado          │
│                                      │
│  5V     ────► VCC encoders           │
│  GND    ────► GND encoders           │
└──────────────────────────────────────┘
```

> **Nota Arduino Uno/Nano:** solo los pines 2 y 3 soportan interrupciones externas.
> Para usar ambos encoders en Uno se necesita la librería **PinChangeInterrupt**.
> Se recomienda **Arduino Mega 2560** para mayor número de pines de interrupción.

---

## Instalación

### 1 · Firmware Arduino

1. Abrir el IDE de Arduino.
2. Instalar la librería **"Encoder" by Paul Stoffregen** desde el Gestor de Librerías.
3. Abrir `arduino/robot_scara_encoder.ino`.
4. Ajustar `L1` y `L2` (longitudes de los eslabones en mm) al inicio del archivo.
5. Compilar y cargar en la placa.

### 2 · Visualizador Python

```bash
# Crear entorno virtual (recomendado)
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Instalar dependencias
pip install -r python/requirements.txt
```

---

## Uso

### Ejecución básica

```bash
# Autodetectar puerto (primer Arduino encontrado) o modo DEMO sin hardware
python python/scara_visualizer.py

# Especificar puerto
python python/scara_visualizer.py --port COM3            # Windows
python python/scara_visualizer.py --port /dev/ttyUSB0   # Linux/macOS

# Especificar longitudes de eslabones
python python/scara_visualizer.py --l1 150 --l2 100

# Ver ayuda completa
python python/scara_visualizer.py --help

# Listar puertos disponibles
python python/scara_visualizer.py --list-ports
```

### Interfaz gráfica

| Botón | Acción |
|---|---|
| **▶ Iniciar Captura** | Empieza a registrar la trayectoria activa |
| **■ Detener Captura** | Finaliza el segmento actual y lo guarda |
| **✖ Limpiar** | Borra trayectoria y todos los segmentos |
| **⬇ Exportar DXF** | Guarda todos los segmentos como archivo `.dxf` |
| **⌂ Home** | Envía comando HOME al Arduino (espera señal Z) |
| **↺ Reset Contadores** | Reinicia los contadores de los encoders a cero |

Los campos **L1** y **L2** permiten cambiar las longitudes de los eslabones en tiempo real (también se envían al Arduino).

---

## Calibración Inicial

1. **Encender** el sistema con el robot en una posición conocida (por ejemplo, ambos eslabones extendidos en la dirección positiva de X).
2. Pulsar **↺ Reset Contadores** (o enviar `R` por el Monitor Serial) para fijar ese punto como origen.
3. Alternativa con señal Z: llevar manualmente cada articulación hasta su marca de referencia y pulsar **⌂ Home**; el sistema espera hasta 3 segundos el pulso Z antes de hacer un reset forzado.

---

## Configurar Longitudes de los Eslabones

### Desde Python (interfaz)
Escribe el valor en milímetros en los campos **L1** y **L2** del panel derecho y pulsa Enter.

### Desde el Monitor Serial de Arduino
```
L1:150.0   ← establece L1 = 150 mm
L2:100.0   ← establece L2 = 100 mm
```

### En el código Arduino (permanente)
Edita las líneas al inicio de `robot_scara_encoder.ino`:
```cpp
float L1 = 150.0;   // mm – longitud eslabón 1
float L2 = 100.0;   // mm – longitud eslabón 2
```

---

## Protocolo de Comunicación Serial

| Dirección | Formato | Descripción |
|---|---|---|
| Arduino → PC | `X:±ddd.dd,Y:±ddd.dd,T1:±ddd.dd,T2:±ddd.dd` | Posición y ángulos |
| Arduino → PC | `# mensaje` | Comentario / log (ignorado por Python) |
| PC → Arduino | `H` | Ejecutar secuencia HOME |
| PC → Arduino | `R` | Reset de contadores |
| PC → Arduino | `S` | Solicitar muestra inmediata |
| PC → Arduino | `L1:xxx.x` | Actualizar longitud eslabón 1 |
| PC → Arduino | `L2:xxx.x` | Actualizar longitud eslabón 2 |

---

## Fórmulas de Cinemática Directa (2R SCARA)

```
X = L1·cos(θ1) + L2·cos(θ1 + θ2)
Y = L1·sin(θ1) + L2·sin(θ1 + θ2)
```

Donde θ1 y θ2 son los ángulos de cada articulación respecto al eslabón anterior.

---

## Modo DEMO (sin hardware)

Si `pyserial` no está instalado o no se detecta ningún puerto, el visualizador genera una trayectoria senoidal sintética para demostrar la interfaz. Se puede usar para explorar los controles sin necesidad de hardware.

---

## Dependencias

| Librería | Versión mínima | Uso |
|---|---|---|
| pyserial | 3.5 | Comunicación serial con Arduino |
| matplotlib | 3.7 | Visualización en tiempo real |
| ezdxf | 1.1 | Exportación a formato DXF |
| numpy | 1.24 | Cálculos numéricos |

---

## Licencia

MIT
