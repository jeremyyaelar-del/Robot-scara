/*
 * Robot SCARA - Lectura de Encoders y Cinemática Directa
 * =========================================================
 * Encoder: E38S6G5-600B-G24N (600 PPR, cuadratura 4x = 2400 cuentas/rev)
 * Plataforma: Arduino Mega 2560 (recomendado) o Arduino Uno/Nano
 *
 * Pines de interrupción disponibles por placa:
 *   Mega  : 2, 3, 18, 19, 20, 21  (usa todos para los 2 encoders)
 *   Uno   : 2, 3  (solo un encoder por hardware; el segundo requiere
 *                  PinChangeInterrupt o reducir a 2x)
 *
 * Conexiones (Mega):
 *   Encoder 1 – Articulación 1:  A → pin 2 | B → pin 3
 *   Encoder 2 – Articulación 2:  A → pin 18| B → pin 19
 *   Señal Z (home) Enc1         → pin 4
 *   Señal Z (home) Enc2         → pin 5
 *   LED de estado               → pin 13
 *
 * Protocolo serial (115200 baud):
 *   Salida: "X:±ddd.dd,Y:±ddd.dd,T1:±ddd.dd,T2:±ddd.dd\n"
 *   Entrada: 'H' → ejecutar secuencia home
 *            'R' → reset contadores (T1=90°, T2=0° – brazo apunta hacia arriba)
 *            'S' → solicitar muestra inmediata
 *            'L1:xxx.x'  → establecer longitud eslabón 1 (mm)
 *            'L2:xxx.x'  → establecer longitud eslabón 2 (mm)
 *            'G1:xxx.xx' → establecer relación de reducción motor 1
 *            'G2:xxx.xx' → establecer relación de reducción motor 2
 *            'ZU:xxx.xx' → mover eje Z hacia arriba xxx mm
 *            'ZD:xxx.xx' → mover eje Z hacia abajo xxx mm
 *            'SZ:xxx.x'  → establecer pasos/mm del eje Z
 */

// ─── Librería de encoders (Paul Stoffregen) ────────────────────────────────
// Instala desde el Gestor de librerías: "Encoder" by Paul Stoffregen
#include <Encoder.h>

// ─── Parámetros configurables ──────────────────────────────────────────────
// Longitudes de los eslabones en milímetros (ajusta según tu robot)
float L1 = 150.0;   // Longitud eslabón 1 [mm]
float L2 = 100.0;   // Longitud eslabón 2 [mm]

// Resolución del encoder con cuadratura 4x: 600 PPR × 4 = 2400 cuentas/rev
const float COUNTS_PER_REV = 2400.0;

// Relación de reducción de cada articulación (ajusta según tu reductor).
// Ejemplo: si el reductor es 10:1, GEAR_RATIO = 10.0
// La fórmula aplicada es: theta = counts / (COUNTS_PER_REV * GEAR_RATIO) * 360
float GEAR_RATIO_1 = 1.0;   // Relación de reducción motor 1
float GEAR_RATIO_2 = 1.0;   // Relación de reducción motor 2

// Velocidad de muestreo: enviar datos cada SAMPLE_INTERVAL ms
const unsigned long SAMPLE_INTERVAL = 20;   // 50 Hz

// Pines de señal Z (home) – conectar a GND a través de resistencia 10 kΩ
const int HOME_PIN_1 = 4;
const int HOME_PIN_2 = 5;

// LED de estado
const int LED_PIN = 13;

// ─── Eje Z (TB6600 Driver) ────────────────────────────────────────────────
const int Z_STEP_PIN = 6;    // STEP- del driver TB6600
const int Z_DIR_PIN  = 7;    // DIR-  del driver TB6600

// Parámetros del eje Z (ajusta según husillo y microstepping de tu TB6600)
// Ejemplo: husillo 2 mm/vuelta, motor 200 pasos/vuelta, microstepping 1/8
//          → STEPS_PER_MM_Z = 200 * 8 / 2 = 800
float STEPS_PER_MM_Z = 100.0;       // pasos/mm
const unsigned int Z_STEP_DELAY_US = 500;  // µs entre pulsos (controla velocidad)

// Posición actual del eje Z en pasos (positivo = subido respecto al home)
long z_steps = 0;

// ─── Objetos de encoder ────────────────────────────────────────────────────
// La librería Encoder usa interrupciones automáticamente en pines válidos
Encoder enc1(2, 3);    // Articulación 1: A=2, B=3
Encoder enc2(18, 19);  // Articulación 2: A=18, B=19

// ─── Variables de estado ───────────────────────────────────────────────────
volatile long count1 = 0;
volatile long count2 = 0;

float theta1_deg = 0.0;
float theta2_deg = 0.0;
float x_pos = 0.0;
float y_pos = 0.0;

bool homeSet = false;
unsigned long lastSampleTime = 0;

// ─── Prototipos ────────────────────────────────────────────────────────────
void doHome();
void moveZ(float mm);
void forwardKinematics(float t1_deg, float t2_deg, float &x, float &y);
void sendData();
void processCommand(String cmd);

// ══════════════════════════════════════════════════════════════════════════
void setup() {
    Serial.begin(115200);
    Serial.setTimeout(100);

    pinMode(HOME_PIN_1, INPUT_PULLUP);
    pinMode(HOME_PIN_2, INPUT_PULLUP);
    pinMode(LED_PIN, OUTPUT);
    pinMode(Z_STEP_PIN, OUTPUT);
    pinMode(Z_DIR_PIN,  OUTPUT);
    digitalWrite(Z_STEP_PIN, LOW);
    digitalWrite(Z_DIR_PIN,  LOW);

    // Parpadeo inicial para indicar arranque
    for (int i = 0; i < 3; i++) {
        digitalWrite(LED_PIN, HIGH);
        delay(150);
        digitalWrite(LED_PIN, LOW);
        delay(150);
    }

    // Reset de contadores
    enc1.write(0);
    enc2.write(0);

    // Aviso por serial
    Serial.println(F("# SCARA Encoder System Ready"));
    Serial.print(F("# L1="));
    Serial.print(L1, 1);
    Serial.print(F("mm  L2="));
    Serial.print(L2, 1);
    Serial.print(F("mm  G1="));
    Serial.print(GEAR_RATIO_1, 2);
    Serial.print(F("  G2="));
    Serial.print(GEAR_RATIO_2, 2);
    Serial.println(F("  Res=2400 cuentas/rev"));
    Serial.print(F("# Z: STEP=pin6  DIR=pin7  SZ="));
    Serial.print(STEPS_PER_MM_Z, 1);
    Serial.println(F(" pasos/mm"));
    Serial.println(F("# Comandos: H=home R=reset(↑) S=muestra L1:x L2:x G1:x G2:x ZU:mm ZD:mm SZ:pasos/mm"));
    digitalWrite(LED_PIN, HIGH);
}

// ══════════════════════════════════════════════════════════════════════════
void loop() {
    // ── Leer encoders ────────────────────────────────────────────────────
    count1 = enc1.read();
    count2 = enc2.read();

    // ── Convertir a ángulos ───────────────────────────────────────────────
    theta1_deg = (float)count1 / (COUNTS_PER_REV * GEAR_RATIO_1) * 360.0;
    theta2_deg = (float)count2 / (COUNTS_PER_REV * GEAR_RATIO_2) * 360.0;

    // ── Cinemática directa ────────────────────────────────────────────────
    forwardKinematics(theta1_deg, theta2_deg, x_pos, y_pos);

    // ── Envío periódico ───────────────────────────────────────────────────
    unsigned long now = millis();
    if (now - lastSampleTime >= SAMPLE_INTERVAL) {
        lastSampleTime = now;
        sendData();
    }

    // ── Procesar comandos entrantes ───────────────────────────────────────
    if (Serial.available() > 0) {
        String cmd = Serial.readStringUntil('\n');
        cmd.trim();
        if (cmd.length() > 0) {
            processCommand(cmd);
        }
    }
}

// ══════════════════════════════════════════════════════════════════════════
/**
 * Cinemática directa del robot SCARA 2R.
 * X = L1·cos(θ1) + L2·cos(θ1+θ2)
 * Y = L1·sin(θ1) + L2·sin(θ1+θ2)
 */
void forwardKinematics(float t1_deg, float t2_deg, float &x, float &y) {
    float t1_rad = t1_deg * DEG_TO_RAD;
    float t2_rad = t2_deg * DEG_TO_RAD;
    x = L1 * cos(t1_rad) + L2 * cos(t1_rad + t2_rad);
    y = L1 * sin(t1_rad) + L2 * sin(t1_rad + t2_rad);
}

// ──────────────────────────────────────────────────────────────────────────
/**
 * Envía los datos en formato legible por Python.
 * Líneas que empiezan con '#' son comentarios y Python las ignora.
 */
void sendData() {
    Serial.print(F("X:"));
    Serial.print(x_pos, 2);
    Serial.print(F(",Y:"));
    Serial.print(y_pos, 2);
    Serial.print(F(",T1:"));
    Serial.print(theta1_deg, 2);
    Serial.print(F(",T2:"));
    Serial.print(theta2_deg, 2);
    Serial.print(F(",Z:"));
    Serial.println((float)z_steps / STEPS_PER_MM_Z, 2);
}

// ──────────────────────────────────────────────────────────────────────────
/**
 * Mueve el eje Z la cantidad indicada en milímetros (bloqueante).
 * mm > 0 → sube (DIR=HIGH), mm < 0 → baja (DIR=LOW).
 * Actualiza z_steps con el desplazamiento realizado.
 */
void moveZ(float mm) {
    long steps = (long)(mm * STEPS_PER_MM_Z);
    if (steps == 0) return;

    digitalWrite(Z_DIR_PIN, steps > 0 ? HIGH : LOW);
    delayMicroseconds(5);   // tiempo de asentamiento de DIR antes del primer pulso

    long absSteps = steps > 0 ? steps : -steps;
    for (long i = 0; i < absSteps; i++) {
        digitalWrite(Z_STEP_PIN, HIGH);
        delayMicroseconds(10);
        digitalWrite(Z_STEP_PIN, LOW);
        delayMicroseconds(Z_STEP_DELAY_US);
    }
    z_steps += steps;
}

// ──────────────────────────────────────────────────────────────────────────
/**
 * Rutina de home: mueve lentamente hasta detectar pulso Z en ambos encoders.
 * Si no hay señal Z conectada, simplemente resetea los contadores.
 */
void doHome() {
    Serial.println(F("# Iniciando secuencia HOME..."));
    digitalWrite(LED_PIN, LOW);

    bool z1Found = false;
    bool z2Found = false;

    // Si la señal Z ya está activa (LOW con pullup), usarla directamente
    if (digitalRead(HOME_PIN_1) == LOW) {
        z1Found = true;
    }
    if (digitalRead(HOME_PIN_2) == LOW) {
        z2Found = true;
    }

    // Esperar hasta 3 segundos por pulso Z (movimiento manual del usuario)
    unsigned long homeStart = millis();
    while ((!z1Found || !z2Found) && (millis() - homeStart < 3000)) {
        if (!z1Found && digitalRead(HOME_PIN_1) == LOW) z1Found = true;
        if (!z2Found && digitalRead(HOME_PIN_2) == LOW) z2Found = true;
        delay(5);
    }

    // Resetear contadores al llegar a home (o forzado por timeout)
    enc1.write(0);
    enc2.write(0);
    homeSet = true;

    if (z1Found && z2Found) {
        Serial.println(F("# HOME completado (señal Z detectada en ambos ejes)"));
    } else {
        Serial.println(F("# HOME completado (reset forzado sin señal Z)"));
    }
    digitalWrite(LED_PIN, HIGH);
}

// ──────────────────────────────────────────────────────────────────────────
/**
 * Interpreta comandos recibidos por serial.
 */
void processCommand(String cmd) {
    if (cmd == "H" || cmd == "h") {
        doHome();

    } else if (cmd == "R" || cmd == "r") {
        // Reset: posicionar el origen angular en T1=90° (brazo apunta hacia +Y)
        enc1.write((long)(COUNTS_PER_REV * GEAR_RATIO_1 / 4.0));
        enc2.write(0);
        Serial.println(F("# Contadores reseteados (T1=90°, T2=0° – apunta hacia arriba)"));

    } else if (cmd == "S" || cmd == "s") {
        sendData();

    } else if (cmd.startsWith("L1:")) {
        float val = cmd.substring(3).toFloat();
        if (val > 0.0) {
            L1 = val;
            Serial.print(F("# L1 = "));
            Serial.print(L1, 1);
            Serial.println(F(" mm"));
        } else {
            Serial.println(F("# ERROR: L1 debe ser > 0"));
        }

    } else if (cmd.startsWith("L2:")) {
        float val = cmd.substring(3).toFloat();
        if (val > 0.0) {
            L2 = val;
            Serial.print(F("# L2 = "));
            Serial.print(L2, 1);
            Serial.println(F(" mm"));
        } else {
            Serial.println(F("# ERROR: L2 debe ser > 0"));
        }

    } else if (cmd.startsWith("G1:")) {
        float val = cmd.substring(3).toFloat();
        if (val > 0.0) {
            GEAR_RATIO_1 = val;
            Serial.print(F("# GEAR_RATIO_1 = "));
            Serial.println(GEAR_RATIO_1, 3);
        } else {
            Serial.println(F("# ERROR: G1 debe ser > 0"));
        }

    } else if (cmd.startsWith("G2:")) {
        float val = cmd.substring(3).toFloat();
        if (val > 0.0) {
            GEAR_RATIO_2 = val;
            Serial.print(F("# GEAR_RATIO_2 = "));
            Serial.println(GEAR_RATIO_2, 3);
        } else {
            Serial.println(F("# ERROR: G2 debe ser > 0"));
        }

    } else if (cmd.startsWith("ZU:")) {
        float mm = cmd.substring(3).toFloat();
        if (mm > 0.0) {
            moveZ(mm);
            Serial.print(F("# Z subido "));
            Serial.print(mm, 2);
            Serial.print(F(" mm → pos="));
            Serial.println((float)z_steps / STEPS_PER_MM_Z, 2);
        } else {
            Serial.println(F("# ERROR: ZU necesita un valor > 0"));
        }

    } else if (cmd.startsWith("ZD:")) {
        float mm = cmd.substring(3).toFloat();
        if (mm > 0.0) {
            moveZ(-mm);
            Serial.print(F("# Z bajado "));
            Serial.print(mm, 2);
            Serial.print(F(" mm → pos="));
            Serial.println((float)z_steps / STEPS_PER_MM_Z, 2);
        } else {
            Serial.println(F("# ERROR: ZD necesita un valor > 0"));
        }

    } else if (cmd.startsWith("SZ:")) {
        float val = cmd.substring(3).toFloat();
        if (val > 0.0) {
            STEPS_PER_MM_Z = val;
            Serial.print(F("# STEPS_PER_MM_Z = "));
            Serial.print(STEPS_PER_MM_Z, 1);
            Serial.println(F(" pasos/mm"));
        } else {
            Serial.println(F("# ERROR: SZ debe ser > 0"));
        }

    } else {
        Serial.print(F("# Comando desconocido: "));
        Serial.println(cmd);
    }
}
