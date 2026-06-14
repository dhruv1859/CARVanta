/*
 * CARVanta Sentinel HYDRA — RP2040 Pin Definitions
 * Matches KiCad schematic: HYDRA_WALKTHROUGH_PART1.md
 * Sheet 3: RP2040 Pin Map
 */

#pragma once

// ─── UART to ESP32 ───────────────────────────────────────
#define PIN_UART_RX         0   // GPIO0 ← ESP32 GPIO1 (TX)
#define PIN_UART_TX         1   // GPIO1 → ESP32 GPIO2 (RX)

// ─── SPI1 — AD5941 Bus ──────────────────────────────────
#define PIN_SPI1_SCK        6   // GPIO6
#define PIN_SPI1_MOSI       7   // GPIO7
#define PIN_SPI1_MISO       8   // GPIO8
#define PIN_AD5941_1_CS     2   // GPIO2  — AFE #1 chip select
#define PIN_AD5941_1_RST    3   // GPIO3  — AFE #1 reset
#define PIN_AD5941_2_CS     4   // GPIO4  — AFE #2 chip select
#define PIN_AD5941_2_RST    5   // GPIO5  — AFE #2 reset
#define PIN_AD5941_1_INT    9   // GPIO9  — AFE #1 interrupt
#define PIN_AD5941_2_INT    10  // GPIO10 — AFE #2 interrupt

// ─── I2C1 — AS7341 + TMP117 ────────────────────────────
#define PIN_I2C1_SDA        12  // GPIO12  (Wire1)
#define PIN_I2C1_SCL        13  // GPIO13  (Wire1)

// ─── Heater PWM ─────────────────────────────────────────
#define PIN_HEATER_PWM      14  // GPIO14 → AO3400 gate

// ─── Excitation LEDs ────────────────────────────────────
#define PIN_UV_LED_EN       15  // GPIO15 → Q3 gate (UV 365nm)
#define PIN_BLUE_LED_EN     16  // GPIO16 → Q4 gate (Blue 470nm)
#define PIN_WHITE_LED_EN    17  // GPIO17 → Q5 gate (White)
