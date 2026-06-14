/*
 * CARVanta Sentinel HYDRA — RP2040 Co-Processor Firmware
 * ═══════════════════════════════════════════════════════
 * Role: Real-time sensor control — AD5941 electrochemistry,
 *       AS7341 spectral, TMP117 thermal, heater PID
 * Communicates with ESP32 via UART (JSON + CRC8)
 *
 * Architecture: Dual-core
 *   Core 0: Command processing, sensor reads
 *   Core 1: Heater PID loop (real-time, 10Hz)
 */

#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>

// ─── Project Headers ────────────────────────────────────
#include "config.h"
#include "pins.h"
#include "drivers/ad5941.h"
#include "drivers/as7341.h"
#include "drivers/tmp117.h"
#include "control/heater_pid.h"
#include "control/led_driver.h"
#include "comms/esp32_protocol.h"

// ─── Global Objects ─────────────────────────────────────
static AD5941        afe1(PIN_AD5941_1_CS, PIN_AD5941_1_RST, PIN_AD5941_1_INT);
static AD5941        afe2(PIN_AD5941_2_CS, PIN_AD5941_2_RST, PIN_AD5941_2_INT);
static AS7341        spectral;
static TMP117        tempSensor;
static HeaterPID     heater;
static LEDDriver     excitationLEDs;
static ESP32Protocol esp32(Serial1);

// ─── Hardware Status Flags ──────────────────────────────
static bool afe1_ok     = false;
static bool afe2_ok     = false;
static bool spectral_ok = false;
static bool temp_ok     = false;

// ─── Command Processing ────────────────────────────────

static void handleRunEchem() {
    StaticJsonDocument<512> data;
    JsonArray ch = data.createNestedArray("channels");

    for (int i = 0; i < 4; i++) {
        float val = afe1_ok ? afe1.runCV(i) : 0.0f;
        ch.add(val);
    }
    for (int i = 0; i < 4; i++) {
        float val = afe2_ok ? afe2.runCV(i) : 0.0f;
        ch.add(val);
    }

    esp32.sendResponse("echem", data);
    Serial.println("[CMD] run_echem complete");
}

static void handleRunEIS() {
    StaticJsonDocument<512> data;
    JsonArray imp = data.createNestedArray("impedance");
    JsonArray pha = data.createNestedArray("phase");

    for (int i = 0; i < 4; i++) {
        float z = 0, p = 0;
        if (afe1_ok) afe1.runEIS(i, 1000.0f, &z, &p);
        imp.add(z);
        pha.add(p);
    }
    for (int i = 0; i < 4; i++) {
        float z = 0, p = 0;
        if (afe2_ok) afe2.runEIS(i, 1000.0f, &z, &p);
        imp.add(z);
        pha.add(p);
    }

    esp32.sendResponse("eis", data);
    Serial.println("[CMD] run_eis complete");
}

static void handleReadSpectral() {
    // Turn on white LED for illumination
    excitationLEDs.enable(ExcitationLED::WHITE);
    delay(50);  // Stabilize

    float channels[11] = {0};
    if (spectral_ok) {
        spectral.readAllChannels(channels);
    }

    excitationLEDs.disable(ExcitationLED::WHITE);

    StaticJsonDocument<512> data;
    JsonArray ch = data.createNestedArray("channels");
    for (int i = 0; i < 11; i++) ch.add(channels[i]);

    esp32.sendResponse("spectral", data);
    Serial.println("[CMD] read_spectral complete");
}

static void handleReadThermal() {
    float temp = temp_ok ? tempSensor.readTemperature() : -999.0f;

    StaticJsonDocument<128> data;
    data["temp"]   = temp;
    data["heater"] = heater.isEnabled() ? heater.getTarget() : 0.0f;

    esp32.sendResponse("thermal", data);
}

static void handleHeaterOn(JsonDocument& cmd) {
    float target = cmd["params"]["temp"] | HEATER_TARGET_TEMP;
    heater.enable(target);
    esp32.sendAck("heater_on");
}

static void handleHeaterOff() {
    heater.disable();
    esp32.sendAck("heater_off");
}

static void handleLED(const char* color, bool on) {
    if (strcmp(color, "led_uv") == 0) {
        if (on) excitationLEDs.enable(ExcitationLED::UV);
        else    excitationLEDs.disable(ExcitationLED::UV);
    } else if (strcmp(color, "led_blue") == 0) {
        if (on) excitationLEDs.enable(ExcitationLED::BLUE);
        else    excitationLEDs.disable(ExcitationLED::BLUE);
    }
    esp32.sendAck(color);
}

static void processCommand(JsonDocument& doc) {
    const char* cmd = doc["cmd"];
    if (!cmd) return;

    if      (strcmp(cmd, "run_echem") == 0)     handleRunEchem();
    else if (strcmp(cmd, "run_eis") == 0)        handleRunEIS();
    else if (strcmp(cmd, "read_spectral") == 0)  handleReadSpectral();
    else if (strcmp(cmd, "read_thermal") == 0)   handleReadThermal();
    else if (strcmp(cmd, "heater_on") == 0)      handleHeaterOn(doc);
    else if (strcmp(cmd, "heater_off") == 0)     handleHeaterOff();
    else if (strncmp(cmd, "led_", 4) == 0) {
        bool on = doc["params"]["on"] | false;
        handleLED(cmd, on);
    }
    else {
        Serial.printf("[CMD] Unknown command: %s\n", cmd);
        esp32.sendError(cmd, "unknown_command");
    }
}

// ─── Core 1: PID Loop (runs on second core) ────────────

static volatile bool core1_ready = false;

void setup1() {
    // Core 1 setup — nothing extra needed
    core1_ready = true;
    Serial.println("[CORE1] PID loop ready");
}

void loop1() {
    // Real-time heater PID at 10Hz
    static unsigned long lastPID = 0;

    if (millis() - lastPID >= HEATER_PID_INTERVAL_MS) {
        lastPID = millis();

        if (heater.isEnabled() && temp_ok) {
            float temp = tempSensor.readTemperature();
            heater.update(temp);
        }
    }

    // LED safety timeout check
    excitationLEDs.update();

    delay(10);
}

// ─── Core 0: Setup ─────────────────────────────────────

void setup() {
    Serial.begin(DEBUG_BAUD_RATE);
    delay(500);
    Serial.println("\n═══════════════════════════════════════");
    Serial.println("  HYDRA RP2040 Co-Processor v" RP_FW_VERSION);
    Serial.println("═══════════════════════════════════════\n");

    // UART to ESP32
    esp32.begin(ESP32_BAUD_RATE, PIN_UART_TX, PIN_UART_RX);
    Serial.println("[INIT] ESP32 UART: OK");

    // SPI1 for AD5941
    SPI1.setSCK(PIN_SPI1_SCK);
    SPI1.setTX(PIN_SPI1_MOSI);
    SPI1.setRX(PIN_SPI1_MISO);
    SPI1.begin();
    Serial.println("[INIT] SPI1 bus: OK");

    // I2C1 for AS7341 + TMP117
    Wire1.setSDA(PIN_I2C1_SDA);
    Wire1.setSCL(PIN_I2C1_SCL);
    Wire1.begin();
    Wire1.setClock(I2C1_CLOCK_HZ);
    Serial.println("[INIT] I2C1 bus: OK");

    // Initialize AD5941 #1
    afe1_ok = afe1.begin(SPI1);
    Serial.printf("[INIT] AD5941 #1: %s\n", afe1_ok ? "OK" : "FAILED");

    // Initialize AD5941 #2
    afe2_ok = afe2.begin(SPI1);
    Serial.printf("[INIT] AD5941 #2: %s\n", afe2_ok ? "OK" : "FAILED");

    // Run calibration on available AFEs
    if (afe1_ok) afe1.calibrate();
    if (afe2_ok) afe2.calibrate();

    // Initialize AS7341
    spectral_ok = spectral.begin(Wire1);
    Serial.printf("[INIT] AS7341 spectral: %s\n", spectral_ok ? "OK" : "FAILED");

    // Initialize TMP117
    temp_ok = tempSensor.begin(Wire1);
    Serial.printf("[INIT] TMP117 temp: %s\n", temp_ok ? "OK" : "FAILED");

    // Heater PID
    heater.begin();
    Serial.println("[INIT] Heater PID: OK");

    // Excitation LEDs
    excitationLEDs.begin();
    Serial.println("[INIT] Excitation LEDs: OK");

    // Wait for Core 1
    while (!core1_ready) delay(1);

    Serial.println("\n[RP2040] ═══ System Ready ═══\n");
}

// ─── Core 0: Main Loop ─────────────────────────────────

void loop() {
    // Process commands from ESP32
    if (esp32.hasCommand()) {
        StaticJsonDocument<512> doc;
        if (esp32.receiveCommand(doc)) {
            processCommand(doc);
        }
    }

    delay(1);
}
