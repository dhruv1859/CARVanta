/*
 * AD5941 Electrochemical AFE Driver — Implementation
 */

#include "ad5941.h"
#include <math.h>

// ─── SPI Low-Level ──────────────────────────────────────

void AD5941::writeReg(uint16_t addr, uint32_t data) {
    _spi->beginTransaction(SPISettings(SPI1_CLOCK_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(_cs, LOW);
    _spi->transfer16(0x0011);          // Write command
    _spi->transfer16(addr);            // Register address
    _spi->transfer16(data >> 16);      // Data high word
    _spi->transfer16(data & 0xFFFF);   // Data low word
    digitalWrite(_cs, HIGH);
    _spi->endTransaction();
}

uint32_t AD5941::readReg(uint16_t addr) {
    _spi->beginTransaction(SPISettings(SPI1_CLOCK_HZ, MSBFIRST, SPI_MODE0));
    digitalWrite(_cs, LOW);
    _spi->transfer16(0x0044);          // Read command
    _spi->transfer16(addr);
    uint32_t data = (uint32_t)_spi->transfer16(0) << 16;
    data |= _spi->transfer16(0);
    digitalWrite(_cs, HIGH);
    _spi->endTransaction();
    return data;
}

// ─── Init & Reset ───────────────────────────────────────

void AD5941::hardwareReset() {
    digitalWrite(_rst, LOW);
    delay(10);
    digitalWrite(_rst, HIGH);
    delay(100);
}

bool AD5941::begin(SPIClass& spi) {
    _spi = &spi;

    pinMode(_cs, OUTPUT);
    pinMode(_rst, OUTPUT);
    pinMode(_int, INPUT);
    digitalWrite(_cs, HIGH);

    hardwareReset();

    // Power up AFE
    enableAFE();

    // Verify chip is responding by reading AFECON
    uint32_t afecon = readReg(AD_REG_AFECON);
    if (afecon == 0 || afecon == 0xFFFFFFFF) return false;

    // Configure TIA with default gain
    configureTIA();

    return true;
}

bool AD5941::isReady() {
    return digitalRead(_int) == LOW;  // INT active low
}

void AD5941::enableAFE() {
    // Power up: enable ADC, DAC, TIA, switch matrix
    writeReg(AD_REG_AFECON, 0x00010000);  // AFE power on
    delay(10);

    // Set bandwidth to full
    writeReg(AD_REG_PMBW, 0x00000001);    // System BW = full
}

// ─── Switch Matrix ──────────────────────────────────────

void AD5941::configureSwitchMatrix(uint8_t channel) {
    // Route AINx to TIA input, CE0 to excitation
    // Bits: AINx select + CE0 enable
    uint32_t swcon = (1UL << channel) | (1UL << 8);
    writeReg(AD_REG_SWCON, swcon);
}

// ─── TIA Configuration ─────────────────────────────────

void AD5941::configureTIA() {
    // HSTIACON register: set RTIA gain
    // Bits [4:0] = RTIA index
    uint32_t tiacon = (_rtiaIndex & 0x1F) | (1UL << 8);  // Enable TIA
    writeReg(AD_REG_HSTIACON, tiacon);
}

void AD5941::setTIAGain(uint8_t gainIndex) {
    if (gainIndex >= AD5941_RTIA_COUNT) gainIndex = AD5941_RTIA_COUNT - 1;
    _rtiaIndex = gainIndex;
    configureTIA();
}

uint8_t AD5941::autoRangeGain(float estimatedCurrent_uA) {
    // Target: ADC voltage should be 20-80% of full scale
    // V_tia = I * R_tia, ADC full scale = 1.82V
    float targetR = (0.5f * 1.82f) / (fabsf(estimatedCurrent_uA) * 1e-6f);

    // Find closest RTIA
    uint8_t bestIdx = 0;
    float bestDiff = 1e12f;
    for (uint8_t i = 0; i < AD5941_RTIA_COUNT; i++) {
        float diff = fabsf(AD5941_RTIA_TABLE[i] - targetR);
        if (diff < bestDiff) {
            bestDiff = diff;
            bestIdx = i;
        }
    }

    setTIAGain(bestIdx);
    return bestIdx;
}

// ─── DAC ────────────────────────────────────────────────

void AD5941::configureDAC(float voltage_mV) {
    // DAC 12-bit, range 0.2V to 2.2V referenced to VBIAS
    // DAC code = (voltage_mV - 200) / (2200 - 200) * 4095
    float normalized = (voltage_mV - 200.0f) / 2000.0f;
    if (normalized < 0.0f) normalized = 0.0f;
    if (normalized > 1.0f) normalized = 1.0f;
    uint16_t dacCode = (uint16_t)(normalized * 4095.0f);

    writeReg(AD_REG_DACCON, 0x00000001);         // Enable DAC
    writeReg(AD_REG_HSTDACON, (uint32_t)dacCode); // Set DAC value
}

// ─── ADC to Current Conversion ──────────────────────────

float AD5941::adcToMicroamps(uint32_t adcRaw) {
    // ADC: 16-bit signed, VREF = 1.82V
    // V_tia = (adcRaw - 32768) * 1.82 / 32768
    // I = V_tia / RTIA
    float voltage = ((int32_t)adcRaw - 32768) * 1.82f / 32768.0f;
    float rtia = AD5941_RTIA_TABLE[_rtiaIndex];
    return (voltage / rtia) * 1e6f;  // Convert to µA
}

// ─── Cyclic Voltammetry ─────────────────────────────────

float AD5941::runCV(uint8_t channel) {
    if (channel > 3) return 0.0f;

    configureSwitchMatrix(channel);
    configureDAC(600.0f);  // Apply 600mV excitation
    configureTIA();

    // Start ADC conversion
    writeReg(AD_REG_ADCCON, 0x00000001);
    writeReg(AD_REG_AFECON, 0x00010002);  // Trigger conversion

    // Wait for conversion complete
    unsigned long start = millis();
    while (!isReady() && millis() - start < 200) {
        delayMicroseconds(100);
    }

    // Read result
    uint32_t adcRaw = readReg(AD_REG_ADCDAT);
    float current = adcToMicroamps(adcRaw);

    // Clear interrupt
    writeReg(AD_REG_INTCCLR, 0xFFFFFFFF);

    return current;
}

// ─── Electrochemical Impedance Spectroscopy ─────────────

void AD5941::runEIS(uint8_t channel, float freqHz, float* impedance, float* phase) {
    if (channel > 3) {
        *impedance = 0;
        *phase = 0;
        return;
    }

    configureSwitchMatrix(channel);

    // Configure waveform generator for sinusoidal excitation
    // Frequency control word: FCW = freq * 2^26 / system_clock
    // System clock = 16MHz (internal)
    uint32_t fcw = (uint32_t)(freqHz * 67108864.0f / 16000000.0f);
    writeReg(AD_REG_WGFCW, fcw);
    writeReg(AD_REG_WGAMPLITUDE, 0x00000199);  // ~10mV amplitude
    writeReg(AD_REG_WGCON, 0x00000005);         // Sine wave, enable

    // Configure DFT engine
    writeReg(AD_REG_DFTCON, 0x00000001);  // Enable DFT, 4096 points

    // Start measurement
    writeReg(AD_REG_AFECON, 0x00010004);

    // Wait for DFT completion (depends on frequency)
    uint16_t waitMs = (uint16_t)(4096.0f / freqHz * 1000.0f) + 50;
    if (waitMs > 5000) waitMs = 5000;
    delay(waitMs);

    // Read DFT real and imaginary
    int32_t dftReal = (int32_t)readReg(AD_REG_DFTREAL);
    int32_t dftImag = (int32_t)readReg(AD_REG_DFTIMAG);

    // Calculate impedance magnitude and phase
    float real = (float)dftReal;
    float imag = (float)dftImag;
    *impedance = sqrtf(real * real + imag * imag);
    *phase     = atan2f(imag, real) * 180.0f / (float)M_PI;

    // Normalize by TIA gain
    float rtia = AD5941_RTIA_TABLE[_rtiaIndex];
    *impedance *= (rtia / 32768.0f);  // Scaled to ohms

    // Disable waveform generator
    writeReg(AD_REG_WGCON, 0x00000000);

    // Clear interrupt
    writeReg(AD_REG_INTCCLR, 0xFFFFFFFF);
}

// ─── Chronoamperometry ──────────────────────────────────

float AD5941::runCA(uint8_t channel, float voltage_mV, uint16_t durationMs) {
    if (channel > 3) return 0.0f;

    configureSwitchMatrix(channel);
    configureDAC(voltage_mV);
    configureTIA();

    // Wait for steady state
    delay(durationMs);

    // Trigger ADC
    writeReg(AD_REG_AFECON, 0x00010002);
    delay(50);

    uint32_t adcRaw = readReg(AD_REG_ADCDAT);
    float current = adcToMicroamps(adcRaw);

    // Turn off DAC
    writeReg(AD_REG_DACCON, 0x00000000);

    return current;
}

// ─── Calibration ────────────────────────────────────────

void AD5941::calibrate() {
    // Route RCAL0/RCAL1 through switch matrix
    writeReg(AD_REG_SWCON, (1UL << 16) | (1UL << 17));  // RCAL path

    // Measure known 10kΩ resistor
    configureDAC(600.0f);
    writeReg(AD_REG_AFECON, 0x00010002);
    delay(100);

    uint32_t adcRaw = readReg(AD_REG_ADCDAT);
    float measuredCurrent = adcToMicroamps(adcRaw);

    if (fabsf(measuredCurrent) > 0.01f) {
        float measuredR = 600.0f / (measuredCurrent * 1e-3f);  // mV / mA = Ω
        float ratio = _rcalValue / measuredR;
        // Store calibration factor (could be saved to flash)
        Serial.printf("[AD5941] RCAL: expected=%.0fΩ measured=%.0fΩ ratio=%.4f\n",
                      _rcalValue, measuredR, ratio);
    }

    // Restore switch matrix
    writeReg(AD_REG_SWCON, 0);
    writeReg(AD_REG_DACCON, 0);
}
