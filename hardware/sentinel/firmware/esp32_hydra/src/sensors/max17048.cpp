/*
 * MAX17048 Fuel Gauge — Implementation
 */

#include "max17048.h"

uint16_t MAX17048::readReg16(uint8_t reg) {
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

void MAX17048::writeReg16(uint8_t reg, uint16_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write((uint8_t)(val >> 8));
    _wire->write((uint8_t)(val & 0xFF));
    _wire->endTransmission();
}

bool MAX17048::begin(TwoWire& wire) {
    _wire = &wire;

    // Check version register (should be non-zero)
    uint16_t version = readReg16(REG_VERSION);
    if (version == 0 || version == 0xFFFF) return false;

    // Set default alert threshold at 15%
    setAlertThreshold(15);

    return true;
}

float MAX17048::getSOC() {
    uint16_t raw = readReg16(REG_SOC);
    // MSB = integer %, LSB = fractional (1/256 %)
    return (float)(raw >> 8) + (float)(raw & 0xFF) / 256.0f;
}

float MAX17048::getVoltage() {
    uint16_t raw = readReg16(REG_VCELL);
    // Resolution: 78.125 µV/cell
    return raw * 78.125e-6f;
}

float MAX17048::getRate() {
    int16_t raw = (int16_t)readReg16(REG_CRATE);
    // Resolution: 0.208 %/hr
    return raw * 0.208f;
}

void MAX17048::setAlertThreshold(uint8_t percent) {
    if (percent > 32) percent = 32;
    uint16_t config = readReg16(REG_CONFIG);
    config = (config & 0xFFE0) | (32 - percent);  // ATHD field is 32 minus threshold
    writeReg16(REG_CONFIG, config);
}

bool MAX17048::isAlertActive() {
    uint16_t config = readReg16(REG_CONFIG);
    return (config & 0x0020) != 0;  // ALRT bit
}

void MAX17048::clearAlert() {
    uint16_t config = readReg16(REG_CONFIG);
    config &= ~0x0020;  // Clear ALRT bit
    writeReg16(REG_CONFIG, config);
}

void MAX17048::quickStart() {
    writeReg16(REG_MODE, 0x4000);  // Quick-Start command
}

void MAX17048::sleep() {
    uint16_t config = readReg16(REG_CONFIG);
    config |= 0x0080;  // SLEEP bit
    writeReg16(REG_CONFIG, config);
}

void MAX17048::wake() {
    uint16_t config = readReg16(REG_CONFIG);
    config &= ~0x0080;
    writeReg16(REG_CONFIG, config);
}
