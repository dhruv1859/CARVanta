/*
 * AD5941 Electrochemical AFE Driver
 * Supports: Cyclic Voltammetry, EIS, Chronoamperometry
 * 4-channel multiplexed via switch matrix
 */

#pragma once

#include <SPI.h>
#include <cstdint>
#include "config.h"

struct CVResult {
    float current_uA;
    float voltage_mV;
};

struct EISResult {
    float impedance_ohm;
    float phase_deg;
    float freq_hz;
};

class AD5941 {
public:
    AD5941(uint8_t cs, uint8_t rst, uint8_t intr)
        : _cs(cs), _rst(rst), _int(intr), _rtiaIndex(7) {}  // default 10kΩ

    bool begin(SPIClass& spi);
    bool isReady();

    // ─── Measurement Modes ──────────────────────────────
    // Cyclic Voltammetry — single channel
    float runCV(uint8_t channel);

    // EIS at a single frequency
    void runEIS(uint8_t channel, float freqHz, float* impedance, float* phase);

    // Chronoamperometry — apply voltage, measure current over time
    float runCA(uint8_t channel, float voltage_mV, uint16_t durationMs);

    // ─── Configuration ──────────────────────────────────
    void setTIAGain(uint8_t gainIndex);  // index into RTIA table
    uint8_t autoRangeGain(float estimatedCurrent_uA);
    void calibrate();  // uses RCAL resistor

    // ─── Low-level ──────────────────────────────────────
    void     writeReg(uint16_t addr, uint32_t data);
    uint32_t readReg(uint16_t addr);
    void     hardwareReset();

private:
    uint8_t   _cs, _rst, _int;
    SPIClass* _spi;
    uint8_t   _rtiaIndex;
    float     _rcalValue = 10000.0f;  // RCAL precision resistor

    void configureSwitchMatrix(uint8_t channel);
    void enableAFE();
    void configureDAC(float voltage_mV);
    void configureTIA();
    float adcToMicroamps(uint32_t adcRaw);
};
