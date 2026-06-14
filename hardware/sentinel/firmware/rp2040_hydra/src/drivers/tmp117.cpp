/*
 * TMP117 High-Precision Temperature Sensor — Implementation
 */

#include "tmp117.h"

void TMP117::writeReg16(uint8_t reg, uint16_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write((uint8_t)(val >> 8));
    _wire->write((uint8_t)(val & 0xFF));
    _wire->endTransmission();
}

uint16_t TMP117::readReg16(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)2);
    if (_wire->available() >= 2) {
        uint8_t msb = _wire->read();
        uint8_t lsb = _wire->read();
        return (uint16_t)(msb << 8) | lsb;
    }
    return 0;
}

bool TMP117::begin(TwoWire& wire) {
    _wire = &wire;

    // Check device ID (should be 0x0117)
    uint16_t id = readReg16(REG_DEVICE_ID);
    if (id != 0x0117) return false;

    // Set continuous conversion mode, 64 averages
    // Config: MOD[1:0]=00 (continuous), AVG[1:0]=10 (64 avg),
    //         CONV[2:0]=100 (1s conversion)
    writeReg16(REG_CONFIG, 0x0220);

    return true;
}

float TMP117::readTemperature() {
    int16_t raw = (int16_t)readReg16(REG_TEMP_RESULT);
    // Resolution: 7.8125 m°C/LSB (1/128 °C)
    return raw * 0.0078125f;
}

void TMP117::setAlertLimits(float low, float high) {
    int16_t lowRaw  = (int16_t)(low / 0.0078125f);
    int16_t highRaw = (int16_t)(high / 0.0078125f);
    writeReg16(REG_HIGH_LIMIT, (uint16_t)highRaw);
    writeReg16(REG_LOW_LIMIT,  (uint16_t)lowRaw);
}

bool TMP117::isAlertActive() {
    uint16_t config = readReg16(REG_CONFIG);
    return (config & 0x8000) != 0;  // Data ready / alert flag
}

void TMP117::setOneShotMode() {
    uint16_t config = readReg16(REG_CONFIG);
    config = (config & 0xF3FF) | 0x0C00;  // MOD = 11 (one-shot)
    writeReg16(REG_CONFIG, config);
}

void TMP117::setContinuousMode() {
    uint16_t config = readReg16(REG_CONFIG);
    config = (config & 0xF3FF);  // MOD = 00 (continuous)
    writeReg16(REG_CONFIG, config);
}
