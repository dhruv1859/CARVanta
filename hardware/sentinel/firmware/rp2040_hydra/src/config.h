/*
 * CARVanta Sentinel HYDRA — RP2040 Configuration
 * System constants, register maps, timing
 */

#pragma once

#include <cstdint>

// ─── VERSION ────────────────────────────────────────────
#define RP_FW_VERSION       "2.0.0"

// ─── COMMUNICATION ──────────────────────────────────────
#define ESP32_BAUD_RATE     921600
#define DEBUG_BAUD_RATE     115200
#define I2C1_CLOCK_HZ      400000
#define SPI1_CLOCK_HZ      4000000   // AD5941 max 16MHz, 4MHz for safety

// ─── I2C ADDRESSES ──────────────────────────────────────
#define I2C_ADDR_AS7341     0x39
#define I2C_ADDR_TMP117     0x48

// ─── HEATER PID DEFAULTS ────────────────────────────────
#define HEATER_TARGET_TEMP  65.0f    // LAMP temperature (°C)
#define HEATER_MAX_TEMP     85.0f    // Safety cutoff (°C)
#define HEATER_MAX_DUTY     230      // Max PWM (0–255), ~90% duty
#define HEATER_PID_INTERVAL_MS  100  // 10 Hz PID loop

#define PID_KP_DEFAULT      50.0f
#define PID_KI_DEFAULT      2.0f
#define PID_KD_DEFAULT      10.0f

// ─── LED SAFETY ─────────────────────────────────────────
#define LED_AUTO_OFF_MS     30000    // Auto-off after 30 seconds

// ─── AD5941 REGISTER MAP ────────────────────────────────
// AFE Control
#define AD_REG_AFECON       0x2000
#define AD_REG_PMBW         0x2004
#define AD_REG_SWCON        0x20A0
#define AD_REG_HSTIACON     0x20A4
#define AD_REG_HSTDACON     0x20A8
#define AD_REG_DACCON       0x20AC
// ADC
#define AD_REG_ADCCON       0x2060
#define AD_REG_ADCDAT       0x2074
#define AD_REG_DFTCON       0x2078   // DFT control
#define AD_REG_DFTREAL      0x2078
#define AD_REG_DFTIMAG      0x207C
#define AD_REG_STATISTIC    0x2080
// Interrupt
#define AD_REG_INTCFLAG     0x2084
#define AD_REG_INTCCLR      0x2088
// Waveform Generator
#define AD_REG_WGFCW        0x2030   // Frequency control word
#define AD_REG_WGAMPLITUDE  0x2034
#define AD_REG_WGOFFSET     0x2038
#define AD_REG_WGCON        0x203C
// Sequencer
#define AD_REG_SEQCON       0x20B4
#define AD_REG_FIFOCON      0x20B8
#define AD_REG_FIFOSRC      0x20BC
#define AD_REG_FIFOSTA      0x20C0
// Calibration
#define AD_REG_CALDATLOCK   0x20C4
#define AD_REG_RCAL         0x20C8

// ─── AD5941 TIA GAIN TABLE (RTIA values) ────────────────
// Index → resistance in ohms
static const float AD5941_RTIA_TABLE[] = {
    200.0f, 1000.0f, 2000.0f, 3000.0f, 4000.0f, 6000.0f,
    8000.0f, 10000.0f, 12000.0f, 16000.0f, 20000.0f,
    24000.0f, 30000.0f, 32000.0f, 40000.0f, 48000.0f,
    64000.0f, 85000.0f, 96000.0f, 100000.0f, 120000.0f,
    128000.0f, 160000.0f, 196000.0f, 256000.0f, 512000.0f
};
#define AD5941_RTIA_COUNT   26
