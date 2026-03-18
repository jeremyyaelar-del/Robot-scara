/**
 * arduino_scara_control.ino
 *
 * Control de robot SCARA de 2 grados de libertad.
 *
 * Hardware:
 *   - 2 motores paso a paso (driver A4988 o DRV8825)
 *   - 2 encoders de cuadratura para retroalimentación
 *
 * Protocolo serial (115200 baudios):
 *   Comandos recibidos:
 *     G0 X<x> Y<y> A<theta1> B<theta2>  → Mover a posición
 *     M0                                 → Parar motores
 *     M100                               → Homing / calibración
 *     M114                               → Reportar posición actual
 *     M220 S<valor>                      → Ajustar velocidad (1-100 %)
 *
 *   Respuestas enviadas:
 *     ok                                 → Comando aceptado
 *     error <mensaje>                    → Error
 *     pos A<theta1> B<theta2> X<x> Y<y>  → Posición actual
 *
 * Parámetros SCARA (modifica según tu robot):
 *   L1 = 150 mm  (brazo 1)
 *   L2 = 120 mm  (brazo 2)
 *
 * Librerías necesarias:
 *   - AccelStepper  (instalar desde el gestor de librerías del IDE Arduino)
 */

#include <AccelStepper.h>

// ============================================================
// Parámetros configurables
// ============================================================

// Longitudes de brazos (mm)
const float L1 = 150.0;
const float L2 = 120.0;

// Pasos por revolución (con microstepping)
// A4988 con 1/16 step: 200 * 16 = 3200 pasos/vuelta
const long STEPS_PER_REV_M1 = 3200;
const long STEPS_PER_REV_M2 = 3200;

// Ángulo en grados por paso
const float DEG_PER_STEP_M1 = 360.0 / STEPS_PER_REV_M1;
const float DEG_PER_STEP_M2 = 360.0 / STEPS_PER_REV_M2;

// Límites de ángulo (grados)
const float THETA1_MIN = -150.0;
const float THETA1_MAX =  150.0;
const float THETA2_MIN = -150.0;
const float THETA2_MAX =  150.0;

// Velocidad y aceleración base
const float BASE_MAX_SPEED    = 800.0;   // pasos/s
const float BASE_ACCELERATION = 400.0;   // pasos/s²

// Pines motor 1 (brazo 1)
const int M1_STEP_PIN = 2;
const int M1_DIR_PIN  = 3;
const int M1_EN_PIN   = 4;

// Pines motor 2 (brazo 2)
const int M2_STEP_PIN = 5;
const int M2_DIR_PIN  = 6;
const int M2_EN_PIN   = 7;

// Pines encoder 1 (brazo 1) — usar pines con interrupción
const int ENC1_A_PIN = 18;
const int ENC1_B_PIN = 19;

// Pines encoder 2 (brazo 2) — usar pines con interrupción
const int ENC2_A_PIN = 20;
const int ENC2_B_PIN = 21;

// Pulsos por revolución del encoder (cuadratura × 4)
const long ENC_PPR = 2000;  // Ajustar según el encoder

// Tamaño del buffer de comandos
const int CMD_BUFFER_SIZE = 32;

// ============================================================
// Variables globales
// ============================================================

AccelStepper motor1(AccelStepper::DRIVER, M1_STEP_PIN, M1_DIR_PIN);
AccelStepper motor2(AccelStepper::DRIVER, M2_STEP_PIN, M2_DIR_PIN);

// Contadores de encoder (actualizados por interrupciones)
volatile long enc1_count = 0;
volatile long enc2_count = 0;

// Ángulos actuales en grados
float current_theta1 = 0.0;
float current_theta2 = 0.0;

// Factor de velocidad (1–100 %)
float speed_factor = 1.0;

// Buffer de entrada serial
char serial_buf[128];
int  serial_buf_idx = 0;

// Flag de homing completado
bool homed = false;

// ============================================================
// Interrupciones de encoders (cuadratura)
// ============================================================

// IRAM_ATTR se usa solo en plataformas ESP32/ESP8266.
// En Arduino Uno/Mega/Due este atributo no existe, se omite.
#ifdef ESP32
  #define ISR_ATTR IRAM_ATTR
#else
  #define ISR_ATTR
#endif

void ISR_ATTR enc1_isr_a() {
    if (digitalRead(ENC1_A_PIN) == digitalRead(ENC1_B_PIN)) {
        enc1_count++;
    } else {
        enc1_count--;
    }
}

void ISR_ATTR enc2_isr_a() {
    if (digitalRead(ENC2_A_PIN) == digitalRead(ENC2_B_PIN)) {
        enc2_count++;
    } else {
        enc2_count--;
    }
}

// ============================================================
// Cinemática directa
// ============================================================

/**
 * Calcula la posición cartesiana (x, y) a partir de los ángulos θ1 y θ2.
 * Los ángulos se expresan en grados.
 */
void forward_kinematics(float theta1_deg, float theta2_deg,
                        float &x_out, float &y_out) {
    float t1 = radians(theta1_deg);
    float t2 = radians(theta2_deg);
    x_out = L1 * cos(t1) + L2 * cos(t1 + t2);
    y_out = L1 * sin(t1) + L2 * sin(t1 + t2);
}

// ============================================================
// Conversión ángulo ↔ pasos
// ============================================================

long degrees_to_steps_m1(float deg) {
    return (long)(deg / DEG_PER_STEP_M1);
}

long degrees_to_steps_m2(float deg) {
    return (long)(deg / DEG_PER_STEP_M2);
}

float encoder_to_degrees_m1() {
    return (float)enc1_count / ENC_PPR * 360.0;
}

float encoder_to_degrees_m2() {
    return (float)enc2_count / ENC_PPR * 360.0;
}

// ============================================================
// Movimiento
// ============================================================

/**
 * Mueve los dos motores a los ángulos indicados (en grados).
 * Bloquea hasta que ambos motores completan el movimiento.
 */
bool move_to_angles(float theta1_deg, float theta2_deg) {
    // Validar límites
    if (theta1_deg < THETA1_MIN || theta1_deg > THETA1_MAX) {
        Serial.println("error theta1 fuera de limites");
        return false;
    }
    if (theta2_deg < THETA2_MIN || theta2_deg > THETA2_MAX) {
        Serial.println("error theta2 fuera de limites");
        return false;
    }

    long target1 = degrees_to_steps_m1(theta1_deg);
    long target2 = degrees_to_steps_m2(theta2_deg);

    motor1.moveTo(target1);
    motor2.moveTo(target2);

    // Ejecutar movimiento de ambos motores en paralelo
    while (motor1.distanceToGo() != 0 || motor2.distanceToGo() != 0) {
        motor1.run();
        motor2.run();
    }

    current_theta1 = theta1_deg;
    current_theta2 = theta2_deg;
    return true;
}

/**
 * Homing: lleva los motores a la posición cero mecánica.
 *
 * PROCEDIMIENTO DE CALIBRACIÓN INICIAL:
 *   1. Con el robot APAGADO, posicionar ambos brazos manualmente en la
 *      posición de referencia (ángulos θ1=0, θ2=0), donde el brazo 1
 *      apunta en la dirección +X y el brazo 2 está extendido también en +X.
 *   2. Con los finales de carrera instalados (conectar a pines libres y
 *      adaptar el código de la sección "// TODO: finales de carrera"):
 *      mover lentamente hacia el final de carrera, detectar el flanco y
 *      marcar ese punto como cero.
 *   3. Sin finales de carrera: asegurarse de que los motores estén
 *      físicamente en la posición cero antes de encender el controlador.
 *
 * NOTA: Esta implementación simplificada asume que la posición cero ya
 * fue establecida mecánicamente al arrancar. En un sistema de producción
 * se deben usar finales de carrera (limit switches) para detectar el home.
 */
void do_homing() {
    Serial.println("Iniciando homing...");

    // Reducir velocidad para homing
    motor1.setMaxSpeed(BASE_MAX_SPEED * 0.3);
    motor2.setMaxSpeed(BASE_MAX_SPEED * 0.3);

    // Mover a posición 0,0 (asumiendo que el cero ya está calibrado)
    motor1.moveTo(0);
    motor2.moveTo(0);
    while (motor1.distanceToGo() != 0 || motor2.distanceToGo() != 0) {
        motor1.run();
        motor2.run();
    }

    // Resetear contadores de encoder
    noInterrupts();
    enc1_count = 0;
    enc2_count = 0;
    interrupts();

    current_theta1 = 0.0;
    current_theta2 = 0.0;
    homed = true;

    // Restaurar velocidad
    apply_speed_factor();

    Serial.println("ok Homing completado");
}

/**
 * Aplica el factor de velocidad a los motores.
 */
void apply_speed_factor() {
    float spd = BASE_MAX_SPEED * speed_factor;
    float acc  = BASE_ACCELERATION * speed_factor;
    motor1.setMaxSpeed(spd);
    motor1.setAcceleration(acc);
    motor2.setMaxSpeed(spd);
    motor2.setAcceleration(acc);
}

// ============================================================
// Parser de comandos
// ============================================================

/**
 * Extrae el valor numérico que sigue a la letra indicada en el string cmd.
 * Devuelve defaultVal si no se encuentra.
 */
float parse_param(const char *cmd, char letter, float default_val) {
    char *ptr = strchr(cmd, letter);
    if (ptr == NULL) return default_val;
    return atof(ptr + 1);
}

/**
 * Procesa una línea de comando recibida por serial.
 */
void process_command(const char *cmd) {
    // Ignorar líneas vacías
    if (strlen(cmd) == 0) return;

    // G0: Movimiento a posición
    if (strncmp(cmd, "G0", 2) == 0) {
        float theta1 = parse_param(cmd, 'A', current_theta1);
        float theta2 = parse_param(cmd, 'B', current_theta2);
        // X e Y se ignoran; los ángulos vienen ya calculados desde Python
        if (move_to_angles(theta1, theta2)) {
            Serial.println("ok");
        }
        return;
    }

    // M0: Parada inmediata
    if (strncmp(cmd, "M0", 2) == 0 && (cmd[2] == '\0' || cmd[2] == ' ')) {
        motor1.stop();
        motor2.stop();
        Serial.println("ok Motores detenidos");
        return;
    }

    // M100: Homing
    if (strncmp(cmd, "M100", 4) == 0) {
        do_homing();
        return;
    }

    // M114: Reportar posición
    if (strncmp(cmd, "M114", 4) == 0) {
        float x, y;
        forward_kinematics(current_theta1, current_theta2, x, y);
        Serial.print("pos A");
        Serial.print(current_theta1, 3);
        Serial.print(" B");
        Serial.print(current_theta2, 3);
        Serial.print(" X");
        Serial.print(x, 3);
        Serial.print(" Y");
        Serial.println(y, 3);
        return;
    }

    // M220: Velocidad
    if (strncmp(cmd, "M220", 4) == 0) {
        float s = parse_param(cmd, 'S', 50.0);
        s = constrain(s, 1.0, 100.0);
        speed_factor = s / 100.0;
        apply_speed_factor();
        Serial.print("ok Velocidad ");
        Serial.print((int)s);
        Serial.println("%");
        return;
    }

    Serial.print("error comando desconocido: ");
    Serial.println(cmd);
}

// ============================================================
// Lectura serial
// ============================================================

void read_serial() {
    while (Serial.available()) {
        char c = (char)Serial.read();
        if (c == '\n' || c == '\r') {
            if (serial_buf_idx > 0) {
                serial_buf[serial_buf_idx] = '\0';
                process_command(serial_buf);
                serial_buf_idx = 0;
            }
        } else if (serial_buf_idx < (int)sizeof(serial_buf) - 1) {
            serial_buf[serial_buf_idx++] = c;
        }
    }
}

// ============================================================
// Setup y loop
// ============================================================

void setup() {
    Serial.begin(115200);

    // Configurar pines de habilitación de motores
    pinMode(M1_EN_PIN, OUTPUT);
    pinMode(M2_EN_PIN, OUTPUT);
    digitalWrite(M1_EN_PIN, LOW);  // LOW = habilitado para A4988/DRV8825
    digitalWrite(M2_EN_PIN, LOW);

    // Configurar encoders
    pinMode(ENC1_A_PIN, INPUT_PULLUP);
    pinMode(ENC1_B_PIN, INPUT_PULLUP);
    pinMode(ENC2_A_PIN, INPUT_PULLUP);
    pinMode(ENC2_B_PIN, INPUT_PULLUP);

    attachInterrupt(digitalPinToInterrupt(ENC1_A_PIN), enc1_isr_a, CHANGE);
    attachInterrupt(digitalPinToInterrupt(ENC2_A_PIN), enc2_isr_a, CHANGE);

    // Configurar AccelStepper
    apply_speed_factor();
    motor1.setCurrentPosition(0);
    motor2.setCurrentPosition(0);

    Serial.println("SCARA ready. Comandos: G0, M0, M100, M114, M220");
}

void loop() {
    read_serial();

    // Mantener motores activos si hay movimiento pendiente
    motor1.run();
    motor2.run();
}
