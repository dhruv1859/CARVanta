/*
 * MAX30102 Pulse Oximeter & Heart Rate Sensor — Implementation
 * Implements SpO2 via RED/IR ratio (Beer-Lambert) and HR via IR peak detection.
 */

#include "max30102.h"
#include <math.h>

// ─── Low-level register access ──────────────────────────

void MAX30102::writeReg(uint8_t reg, uint8_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write(val);
    _wire->endTransmission();
}

uint8_t MAX30102::readReg(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)1);
    return _wire->available() ? _wire->read() : 0;
}

void MAX30102::readMulti(uint8_t reg, uint8_t* buf, uint8_t len) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, len);
    for (uint8_t i = 0; i < len && _wire->available(); i++) {
        buf[i] = _wire->read();
    }
}

// ─── Initialization ─────────────────────────────────────

bool MAX30102::begin(TwoWire& wire) {
    _wire = &wire;

    // Check part ID
    if (readReg(REG_PART_ID) != 0x15) return false;

    // Reset
    writeReg(REG_MODE_CONFIG, 0x40);
    delay(50);

    // Clear FIFO pointers
    writeReg(REG_FIFO_WR_PTR, 0);
    writeReg(REG_OVF_COUNTER, 0);
    writeReg(REG_FIFO_RD_PTR, 0);

    // FIFO config: sample averaging=4, FIFO rollover enable
    writeReg(REG_FIFO_CONFIG, 0x4F);

    // Mode: SpO2 mode (Red + IR LEDs)
    writeReg(REG_MODE_CONFIG, 0x03);

    // SpO2 config: ADC range 4096nA, 100 SPS, 411µs pulse width
    writeReg(REG_SPO2_CONFIG, 0x27);

    // LED currents: 6.4mA Red, 6.4mA IR (conservative start)
    writeReg(REG_LED1_PA, 0x20);
    writeReg(REG_LED2_PA, 0x20);

    // Enable FIFO almost full interrupt
    writeReg(REG_INT_ENABLE1, 0xC0);

    return true;
}

void MAX30102::shutdown() {
    uint8_t mode = readReg(REG_MODE_CONFIG);
    writeReg(REG_MODE_CONFIG, mode | 0x80);  // SHDN bit
}

void MAX30102::wakeup() {
    uint8_t mode = readReg(REG_MODE_CONFIG);
    writeReg(REG_MODE_CONFIG, mode & ~0x80);
}

void MAX30102::setLEDCurrent(uint8_t redMA, uint8_t irMA) {
    // Each step = 0.2mA, max 51mA (0xFF)
    writeReg(REG_LED1_PA, (uint8_t)(redMA / 0.2f));
    writeReg(REG_LED2_PA, (uint8_t)(irMA / 0.2f));
}

void MAX30102::setSampleRate(uint16_t rate) {
    uint8_t val = readReg(REG_SPO2_CONFIG) & 0xE3;
    uint8_t bits = 0;
    switch (rate) {
        case 50:   bits = 0; break;
        case 100:  bits = 1; break;
        case 200:  bits = 2; break;
        case 400:  bits = 3; break;
        case 800:  bits = 4; break;
        case 1000: bits = 5; break;
        case 1600: bits = 6; break;
        case 3200: bits = 7; break;
        default:   bits = 1; break;
    }
    writeReg(REG_SPO2_CONFIG, val | (bits << 2));
}

void MAX30102::setPulseWidth(uint16_t us) {
    uint8_t val = readReg(REG_SPO2_CONFIG) & 0xFC;
    uint8_t bits = 0;
    switch (us) {
        case 69:  bits = 0; break;
        case 118: bits = 1; break;
        case 215: bits = 2; break;
        case 411: bits = 3; break;
        default:  bits = 3; break;
    }
    writeReg(REG_SPO2_CONFIG, val | bits);
}

// ─── FIFO Read ──────────────────────────────────────────

uint16_t MAX30102::readFIFO(uint32_t* redBuf, uint32_t* irBuf, uint16_t maxSamples) {
    uint8_t wrPtr = readReg(REG_FIFO_WR_PTR);
    uint8_t rdPtr = readReg(REG_FIFO_RD_PTR);

    int16_t numSamples = wrPtr - rdPtr;
    if (numSamples < 0) numSamples += 32;
    if (numSamples == 0) return 0;
    if (numSamples > (int16_t)maxSamples) numSamples = maxSamples;

    uint16_t count = 0;
    for (int16_t i = 0; i < numSamples; i++) {
        uint8_t buf[6];
        readMulti(REG_FIFO_DATA, buf, 6);

        // 18-bit samples, MSB first, top 2 bits unused
        redBuf[count] = ((uint32_t)(buf[0] & 0x03) << 16) |
                        ((uint32_t)buf[1] << 8) | buf[2];
        irBuf[count]  = ((uint32_t)(buf[3] & 0x03) << 16) |
                        ((uint32_t)buf[4] << 8) | buf[5];
        count++;
    }
    return count;
}

// ─── SpO2 Algorithm ─────────────────────────────────────

float MAX30102::calculateRatio(uint32_t* red, uint32_t* ir, uint16_t len) {
    if (len < 10) return -1.0f;

    // Calculate AC and DC components
    float redDC = 0, irDC = 0;
    for (uint16_t i = 0; i < len; i++) {
        redDC += red[i];
        irDC  += ir[i];
    }
    redDC /= len;
    irDC  /= len;

    if (redDC < 1000 || irDC < 1000) return -1.0f;  // finger not detected

    float redAC = 0, irAC = 0;
    for (uint16_t i = 0; i < len; i++) {
        float rd = (float)red[i] - redDC;
        float id = (float)ir[i]  - irDC;
        redAC += rd * rd;
        irAC  += id * id;
    }
    redAC = sqrtf(redAC / len);
    irAC  = sqrtf(irAC / len);

    if (irAC < 1.0f) return -1.0f;

    // R = (ACred/DCred) / (ACir/DCir)
    return (redAC / redDC) / (irAC / irDC);
}

float MAX30102::ratioToSpO2(float ratio) {
    // Empirical lookup: SpO2 = 110 - 25 * R  (linear approximation)
    // Valid for R in range 0.4 to 3.4
    if (ratio < 0.0f) return -1.0f;
    float spo2 = 110.0f - 25.0f * ratio;
    if (spo2 > 100.0f) spo2 = 100.0f;
    if (spo2 < 0.0f) spo2 = 0.0f;
    return spo2;
}

float MAX30102::detectHeartRate(uint32_t* ir, uint16_t len, uint16_t sampleRate) {
    if (len < 50) return -1.0f;

    // Simple peak detection on IR signal
    // Find average, then count threshold crossings (rising edge)
    float avg = 0;
    for (uint16_t i = 0; i < len; i++) avg += ir[i];
    avg /= len;

    // Find max deviation for threshold
    float maxDev = 0;
    for (uint16_t i = 0; i < len; i++) {
        float dev = fabsf((float)ir[i] - avg);
        if (dev > maxDev) maxDev = dev;
    }

    float threshold = avg + maxDev * 0.3f;
    uint16_t peaks = 0;
    bool aboveThreshold = false;
    uint16_t minPeakDistance = sampleRate / 4;  // max 240 BPM
    uint16_t lastPeak = 0;

    for (uint16_t i = 1; i < len; i++) {
        if (ir[i] > threshold && !aboveThreshold) {
            if (i - lastPeak > minPeakDistance) {
                peaks++;
                lastPeak = i;
            }
            aboveThreshold = true;
        } else if (ir[i] < threshold) {
            aboveThreshold = false;
        }
    }

    if (peaks < 2) return -1.0f;

    float durationSec = (float)len / sampleRate;
    return (peaks / durationSec) * 60.0f;  // BPM
}

// ─── High-level read ────────────────────────────────────

bool MAX30102::readSpO2(float* spo2, float* heartRate, uint16_t sampleDurationMs) {
    // Clear FIFO
    writeReg(REG_FIFO_WR_PTR, 0);
    writeReg(REG_OVF_COUNTER, 0);
    writeReg(REG_FIFO_RD_PTR, 0);

    // Collect samples for the specified duration
    delay(sampleDurationMs);

    static uint32_t redBuf[256], irBuf[256];
    uint16_t totalSamples = 0;

    // Read all available FIFO data
    uint16_t n = readFIFO(redBuf, irBuf, 256);
    totalSamples = n;

    if (totalSamples < 50) {
        *spo2 = -1.0f;
        *heartRate = -1.0f;
        return false;
    }

    float ratio = calculateRatio(redBuf, irBuf, totalSamples);
    *spo2 = ratioToSpO2(ratio);
    *heartRate = detectHeartRate(irBuf, totalSamples, 100);  // 100 SPS default

    return (*spo2 > 0 && *heartRate > 0);
}
