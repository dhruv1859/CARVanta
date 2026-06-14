/*
 * CARVanta Sentinel HYDRA — ESP32-S3 Configuration
 * System constants, I2C addresses, timing, feature flags
 */

#pragma once

#include <cstdint>

// ─── VERSION ────────────────────────────────────────────
#define FW_VERSION          "2.0.0"
#define FW_BUILD_DATE       __DATE__
#define DEVICE_ID_PREFIX    "HYDRA"

// ─── FEATURE FLAGS ──────────────────────────────────────
#define ENABLE_OTA          1
#define ENABLE_CLOUD        1
#define ENABLE_SD_LOGGING   1
#define ENABLE_DISPLAY      1
#define ENABLE_WATCHDOG     1

// ─── COMMUNICATION ──────────────────────────────────────
#define RP2040_BAUD_RATE    921600
#define USB_SERIAL_BAUD     115200
#define I2C_CLOCK_HZ        400000

// ─── I2C ADDRESSES ──────────────────────────────────────
#define I2C_ADDR_TCA9548A   0x70  // I2C Mux
#define I2C_ADDR_MAX30102   0x57  // SpO2 (Mux Ch0)
#define I2C_ADDR_MLX90614   0x5A  // IR Temp (Mux Ch1)
#define I2C_ADDR_DS3231     0x68  // RTC (Mux Ch2)
#define I2C_ADDR_LSM6DSO    0x6A  // IMU (Mux Ch3)
#define I2C_ADDR_MAX17048   0x36  // Fuel Gauge (direct, no mux)
#define I2C_ADDR_BQ25895    0x6B  // Charger (direct, no mux)

// ─── TCA9548A MUX CHANNEL MAP ───────────────────────────
#define MUX_CH_MAX30102     0
#define MUX_CH_MLX90614     1
#define MUX_CH_DS3231       2
#define MUX_CH_LSM6DSO      3
// Channels 4–7 spare

// ─── TIMING ─────────────────────────────────────────────
#define MEASUREMENT_INTERVAL_MS     30000   // 30 seconds
#define DISPLAY_REFRESH_MS          1000    // 1 second
#define CLOUD_UPLOAD_INTERVAL_MS    60000   // 1 minute
#define WIFI_CONNECT_TIMEOUT_MS     10000   // 10 seconds
#define RP2040_CMD_TIMEOUT_MS       5000    // 5 second command timeout
#define RP2040_RETRY_COUNT          3       // retry failed commands
#define WATCHDOG_TIMEOUT_S          30      // 30 second WDT

// ─── CLOUD ──────────────────────────────────────────────
#define API_ENDPOINT        "https://carvanta-api.up.railway.app/api/v1/sentinel/upload"
#define OTA_CHECK_ENDPOINT  "https://carvanta-api.up.railway.app/api/v1/sentinel/ota"
#define CLOUD_RETRY_MAX     5
#define CLOUD_BACKOFF_BASE_MS   1000  // exponential backoff base

// ─── DISPLAY ────────────────────────────────────────────
#define TFT_WIDTH           240
#define TFT_HEIGHT          320
#define TFT_BACKLIGHT_PWM   200  // 0–255

// ─── BATTERY ────────────────────────────────────────────
#define BATTERY_LOW_THRESHOLD   15.0f  // % SOC
#define BATTERY_CRITICAL        5.0f   // % SOC → deep sleep

// ─── SD CARD ────────────────────────────────────────────
#define SD_LOG_DIR          "/hydra_logs"
#define SD_MAX_FILE_SIZE    (5 * 1024 * 1024)  // 5MB per file

// ─── SENSOR DATA STRUCTURE ──────────────────────────────
struct SensorReading {
    // Electrochemical (from RP2040 via UART)
    float echem_channels[8];     // AD5941 CV current (µA)
    float eis_impedance[8];      // EIS impedance (Ω)
    float eis_phase[8];          // EIS phase (degrees)

    // Spectral (from RP2040 via UART)
    float spectral[11];          // AS7341 11-channel (counts)

    // Thermal (from RP2040 via UART)
    float precision_temp;        // TMP117 (°C)
    float heater_temp;           // Heater zone (°C)

    // Vitals (read directly via I2C mux)
    float spo2;                  // MAX30102 (%)
    float heart_rate;            // MAX30102 (BPM)
    float ir_object_temp;        // MLX90614 object (°C)
    float ir_ambient_temp;       // MLX90614 ambient (°C)

    // Motion (read directly via I2C mux)
    float accel[3];              // LSM6DSO (g)
    float gyro[3];               // LSM6DSO (dps)

    // Power
    float battery_soc;           // MAX17048 (%)
    float battery_voltage;       // MAX17048 (V)
    float battery_rate;          // MAX17048 (%/hr)

    // Timestamp
    uint32_t timestamp;          // DS3231 epoch
    uint8_t  year, month, day;
    uint8_t  hour, minute, second;

    // Flags
    bool     echem_valid;
    bool     eis_valid;
    bool     spectral_valid;
    bool     thermal_valid;
    bool     vitals_valid;
    bool     motion_valid;
};
