/*
 * CARVanta Sentinel HYDRA — ESP32-S3 Pin Definitions
 * Matches KiCad schematic: HYDRA_WALKTHROUGH_PART1.md
 * Sheet 2: ESP32 Pin Map
 */

#pragma once

// ─── UART to RP2040 ──────────────────────────────────────
#define PIN_UART_TX         1   // GPIO1 → RP2040 GPIO0 (RX)
#define PIN_UART_RX         2   // GPIO2 ← RP2040 GPIO1 (TX)

// ─── I2C Main Bus (→ TCA9548A Mux) ──────────────────────
#define PIN_I2C_SDA         5   // GPIO5
#define PIN_I2C_SCL         6   // GPIO6

// ─── SPI0 (TFT Display + SD Card) ───────────────────────
#define PIN_SPI0_MOSI       11  // GPIO11
#define PIN_SPI0_SCK        12  // GPIO12
#define PIN_SPI0_MISO       13  // GPIO13
#define PIN_TFT_CS          8   // GPIO8
#define PIN_TFT_DC          7   // GPIO7
#define PIN_TFT_RST         9   // GPIO9
#define PIN_TFT_BL          10  // GPIO10
#define PIN_SD_CS           14  // GPIO14

// ─── UI: LEDs + Buzzer ──────────────────────────────────
#define PIN_LED_DATA        3   // GPIO3 → WS2812B D1 DIN
#define PIN_BUZZER          4   // GPIO4 → Q1 gate (buzzer driver)
#define NUM_WS2812B_LEDS    4   // D1–D4

// ─── Status Inputs ──────────────────────────────────────
#define PIN_CHG_INT         15  // GPIO15 ← BQ25895 INT (charge status)
#define PIN_BATT_ALT        16  // GPIO16 ← MAX17048 ALT (low battery)
#define PIN_PG_3V3          17  // GPIO17 ← TPS63020 PG (power good)

// ─── USB (Hardware-fixed, cannot remap) ──────────────────
#define PIN_USB_DM          19  // GPIO19 — USB D−
#define PIN_USB_DP          20  // GPIO20 — USB D+
