/*
 * CARVanta Sentinel HYDRA — ESP32-S3 Main Firmware
 * ═══════════════════════════════════════════════════
 * Role: Brain MCU — WiFi/BLE, Display, Cloud Upload, AI Inference
 * Communicates with RP2040 co-processor via UART (JSON + CRC8)
 *
 * Architecture: FreeRTOS tasks on dual cores
 *   Core 0: WiFi, cloud upload, OTA
 *   Core 1: Sensors, display, measurement cycles
 */

#include <Arduino.h>
#include <Wire.h>
#include <SPI.h>

// ─── Project Headers ────────────────────────────────────
#include "config.h"
#include "pins.h"
#include "comms/rp2040_protocol.h"
#include "comms/cloud_client.h"
#include "sensors/i2c_mux.h"
#include "sensors/max30102.h"
#include "sensors/mlx90614.h"
#include "sensors/ds3231.h"
#include "sensors/lsm6dso.h"
#include "sensors/max17048.h"
#include "ui/display.h"
#include "ui/leds.h"
#include "ui/buzzer.h"
#include "storage/sd_logger.h"
#include "system/power_manager.h"
#include "system/watchdog.h"
#include "system/ota_updater.h"

// ─── Global Objects ─────────────────────────────────────
static RP2040Link    rp2040(Serial1);
static CloudClient   cloud;
static TCA9548A      mux(I2C_ADDR_TCA9548A);
static MAX30102      spo2Sensor(I2C_ADDR_MAX30102);
static MLX90614      irTemp(I2C_ADDR_MLX90614);
static DS3231        rtc(I2C_ADDR_DS3231);
static LSM6DSO       imu(I2C_ADDR_LSM6DSO);
static MAX17048      fuelGauge(I2C_ADDR_MAX17048);
static Display       display;
static StatusLEDs    leds;
static Buzzer        buzzer;
static SDLogger      sdLogger;
static PowerManager  power;
static Watchdog      wdt;
static OTAUpdater    ota;

// ─── Shared State ───────────────────────────────────────
static SensorReading currentReading;
static SemaphoreHandle_t readingMutex;
static volatile bool     measurementRequested = false;

// WiFi credentials (update these or load from NVS)
static const char* WIFI_SSID = "YOUR_SSID";
static const char* WIFI_PASS = "YOUR_PASSWORD";

// ─── Sensor Initialization ─────────────────────────────

static bool initSensors() {
    Serial.println("[INIT] Initializing sensors...");
    bool allOk = true;

    // I2C Mux
    if (mux.begin(Wire)) {
        Serial.println("[INIT] TCA9548A mux: OK");
    } else {
        Serial.println("[INIT] TCA9548A mux: FAILED");
        allOk = false;
    }

    // MAX30102 (Mux Ch0)
    mux.selectChannel(MUX_CH_MAX30102);
    if (spo2Sensor.begin(Wire)) {
        Serial.println("[INIT] MAX30102 SpO2: OK");
    } else {
        Serial.println("[INIT] MAX30102 SpO2: FAILED");
        allOk = false;
    }

    // MLX90614 (Mux Ch1)
    mux.selectChannel(MUX_CH_MLX90614);
    if (irTemp.begin(Wire)) {
        Serial.println("[INIT] MLX90614 IR temp: OK");
    } else {
        Serial.println("[INIT] MLX90614 IR temp: FAILED");
        allOk = false;
    }

    // DS3231 (Mux Ch2)
    mux.selectChannel(MUX_CH_DS3231);
    if (rtc.begin(Wire)) {
        Serial.println("[INIT] DS3231 RTC: OK");
    } else {
        Serial.println("[INIT] DS3231 RTC: FAILED");
        allOk = false;
    }

    // LSM6DSO (Mux Ch3)
    mux.selectChannel(MUX_CH_LSM6DSO);
    if (imu.begin(Wire)) {
        Serial.println("[INIT] LSM6DSO IMU: OK");
    } else {
        Serial.println("[INIT] LSM6DSO IMU: FAILED");
        allOk = false;
    }

    mux.disableAll();

    // MAX17048 (direct on I2C, no mux)
    if (fuelGauge.begin(Wire)) {
        Serial.println("[INIT] MAX17048 fuel gauge: OK");
    } else {
        Serial.println("[INIT] MAX17048 fuel gauge: FAILED");
        allOk = false;
    }

    return allOk;
}

// ─── Measurement Cycle ─────────────────────────────────

static void runMeasurementCycle() {
    Serial.println("[MEAS] Starting measurement cycle...");
    leds.setMode(LEDMode::MEASURING);

    xSemaphoreTake(readingMutex, portMAX_DELAY);

    // 1. Electrochemical sweep (RP2040)
    display.showMeasuring("Electrochemical");
    currentReading.echem_valid = rp2040.requestEchem(currentReading.echem_channels);

    // 2. EIS (RP2040)
    display.showMeasuring("Impedance");
    currentReading.eis_valid = rp2040.requestEIS(
        currentReading.eis_impedance, currentReading.eis_phase);

    // 3. Spectral (RP2040)
    display.showMeasuring("Spectral");
    currentReading.spectral_valid = rp2040.requestSpectral(currentReading.spectral);

    // 4. Thermal (RP2040)
    display.showMeasuring("Thermal");
    currentReading.thermal_valid = rp2040.requestThermal(
        &currentReading.precision_temp, &currentReading.heater_temp);

    // 5. SpO2 + Heart Rate (direct I2C via mux)
    display.showMeasuring("Vitals");
    mux.selectChannel(MUX_CH_MAX30102);
    currentReading.vitals_valid = spo2Sensor.readSpO2(
        &currentReading.spo2, &currentReading.heart_rate, 4000);

    // 6. IR Temperature
    mux.selectChannel(MUX_CH_MLX90614);
    currentReading.ir_object_temp = irTemp.readObjectTemp();
    currentReading.ir_ambient_temp = irTemp.readAmbientTemp();

    // 7. RTC Timestamp
    mux.selectChannel(MUX_CH_DS3231);
    DateTime dt = rtc.getDateTime();
    currentReading.timestamp = rtc.getEpoch();
    currentReading.year   = dt.year - 2000;
    currentReading.month  = dt.month;
    currentReading.day    = dt.day;
    currentReading.hour   = dt.hour;
    currentReading.minute = dt.minute;
    currentReading.second = dt.second;

    // 8. IMU
    mux.selectChannel(MUX_CH_LSM6DSO);
    imu.readAccel(currentReading.accel[0], currentReading.accel[1], currentReading.accel[2]);
    imu.readGyro(currentReading.gyro[0], currentReading.gyro[1], currentReading.gyro[2]);
    currentReading.motion_valid = true;

    mux.disableAll();

    // 9. Battery
    currentReading.battery_soc     = fuelGauge.getSOC();
    currentReading.battery_voltage = fuelGauge.getVoltage();
    currentReading.battery_rate    = fuelGauge.getRate();

    xSemaphoreGive(readingMutex);

    // 10. Display results
    display.showDashboard(currentReading);

    // 11. Log to SD
    if (sdLogger.isReady()) {
        sdLogger.logReading(currentReading);
    }

    // 12. Upload to cloud (done in cloud task)

    leds.setMode(LEDMode::SUCCESS);
    buzzer.successBeep();
    Serial.println("[MEAS] Measurement cycle complete.");
}

// ─── FreeRTOS Tasks ─────────────────────────────────────

// Task: Measurement + Display (Core 1)
static void taskMeasurement(void* param) {
    TickType_t lastWake = xTaskGetTickCount();

    for (;;) {
        wdt.feed();
        runMeasurementCycle();
        vTaskDelayUntil(&lastWake, pdMS_TO_TICKS(MEASUREMENT_INTERVAL_MS));
    }
}

// Task: Cloud Upload (Core 0)
static void taskCloudUpload(void* param) {
    TickType_t lastUpload = xTaskGetTickCount();

    for (;;) {
        vTaskDelayUntil(&lastUpload, pdMS_TO_TICKS(CLOUD_UPLOAD_INTERVAL_MS));

        if (!cloud.isConnected()) {
            cloud.connectWiFi();
        }

        xSemaphoreTake(readingMutex, portMAX_DELAY);
        SensorReading snapshot = currentReading;
        xSemaphoreGive(readingMutex);

        if (cloud.uploadReading(snapshot)) {
            Serial.println("[CLOUD] Upload successful");
        } else {
            Serial.println("[CLOUD] Upload failed");
        }
    }
}

// Task: UI Updates (Core 1)
static void taskUI(void* param) {
    for (;;) {
        leds.update();
        buzzer.update();
        ota.handle();

        // Check battery
        float soc = fuelGauge.getSOC();
        if (soc < BATTERY_LOW_THRESHOLD && soc > BATTERY_CRITICAL) {
            leds.setMode(LEDMode::LOW_BATTERY);
            display.showError("LOW BATTERY!");
        }
        power.checkCriticalBattery(soc);

        vTaskDelay(pdMS_TO_TICKS(33));  // ~30fps
    }
}

// ─── SETUP ──────────────────────────────────────────────

void setup() {
    Serial.begin(USB_SERIAL_BAUD);
    delay(500);
    Serial.println("\n═══════════════════════════════════════");
    Serial.println("  CARVanta Sentinel HYDRA v" FW_VERSION);
    Serial.println("  Multimodal Diagnostic Engine");
    Serial.println("═══════════════════════════════════════\n");

    // Create mutex
    readingMutex = xSemaphoreCreateMutex();

    // Initialize subsystems
    Serial.println("[INIT] Peripherals...");

    // UART to RP2040
    rp2040.begin(RP2040_BAUD_RATE, PIN_UART_RX, PIN_UART_TX);
    Serial.println("[INIT] RP2040 UART: OK");

    // I2C
    Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL);
    Wire.setClock(I2C_CLOCK_HZ);
    Serial.println("[INIT] I2C bus: OK");

    // SPI (for SD card — TFT uses its own SPI in TFT_eSPI)
    SPI.begin(PIN_SPI0_SCK, PIN_SPI0_MISO, PIN_SPI0_MOSI);

    // Display
    display.begin();
    display.showSplash();
    Serial.println("[INIT] TFT display: OK");

    // LEDs
    leds.begin();
    leds.setMode(LEDMode::IDLE);
    Serial.println("[INIT] WS2812B LEDs: OK");

    // Buzzer
    buzzer.begin();
    Serial.println("[INIT] Buzzer: OK");

    // Power manager
    power.begin();
    Serial.println("[INIT] Power manager: OK");

    // SD Card
    if (sdLogger.begin(PIN_SD_CS)) {
        Serial.println("[INIT] SD card: OK");
    } else {
        Serial.println("[INIT] SD card: NOT FOUND (logging disabled)");
    }

    // Sensors (via I2C mux)
    bool sensorsOk = initSensors();

    // WiFi
    cloud.begin(WIFI_SSID, WIFI_PASS);
    if (cloud.connectWiFi()) {
        Serial.printf("[INIT] WiFi connected: %s\n", WiFi.localIP().toString().c_str());
        display.showWiFiStatus(true, WiFi.localIP().toString().c_str());
    } else {
        Serial.println("[INIT] WiFi: FAILED (offline mode)");
        display.showWiFiStatus(false);
    }

    // OTA
    ota.begin();
    Serial.println("[INIT] OTA updater: OK");

    // Watchdog
    wdt.begin();
    Serial.println("[INIT] Watchdog: OK");

    // Boot chime
    buzzer.bootChime();

    delay(2000);
    Serial.println("\n[HYDRA] ═══ System Ready ═══\n");

    // ─── Launch FreeRTOS Tasks ──────────────────────────
    xTaskCreatePinnedToCore(taskMeasurement, "Measure", 8192, NULL, 2, NULL, 1);
    xTaskCreatePinnedToCore(taskCloudUpload, "Cloud",   4096, NULL, 1, NULL, 0);
    xTaskCreatePinnedToCore(taskUI,          "UI",      4096, NULL, 1, NULL, 1);
}

// ─── LOOP (unused — all work done in FreeRTOS tasks) ────

void loop() {
    vTaskDelay(pdMS_TO_TICKS(1000));
}
