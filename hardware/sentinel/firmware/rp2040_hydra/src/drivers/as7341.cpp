/*
 * AS7341 11-Channel Spectral Sensor — Implementation
 * Channels: F1(415nm), F2(445nm), F3(480nm), F4(515nm),
 *           F5(555nm), F6(590nm), F7(630nm), F8(680nm),
 *           Clear, NIR(910nm), Flicker
 */

#include "as7341.h"

// ─── Low-Level Register Access ──────────────────────────

void AS7341::writeReg(uint8_t reg, uint8_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write(val);
    _wire->endTransmission();
}

uint8_t AS7341::readReg(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)1);
    return _wire->available() ? _wire->read() : 0;
}

uint16_t AS7341::readReg16(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)2);
    if (_wire->available() >= 2) {
        uint8_t lsb = _wire->read();
        uint8_t msb = _wire->read();
        return (uint16_t)(msb << 8) | lsb;
    }
    return 0;
}

// ─── Initialization ─────────────────────────────────────

bool AS7341::begin(TwoWire& wire) {
    _wire = &wire;

    // Check device ID (should be 0x24 for AS7341)
    uint8_t id = readReg(REG_ID);
    if ((id & 0xFC) != 0x24) return false;  // Mask lower 2 bits

    // Power on
    writeReg(REG_ENABLE, 0x01);  // PON
    delay(10);

    // Set default integration time: ATIME=29 → ~83ms
    setIntegrationTime(29);

    // Set default gain: 8x
    setGain(3);

    return true;
}

// ─── Configuration ──────────────────────────────────────

void AS7341::setIntegrationTime(uint8_t atime) {
    writeReg(REG_ATIME, atime);
}

void AS7341::setGain(uint8_t gain) {
    if (gain > 10) gain = 10;
    writeReg(REG_CFG1, gain);  // AGAIN field
}

void AS7341::enableFlickerDetection(bool enable) {
    uint8_t cfg9 = readReg(REG_CFG9);
    if (enable)
        cfg9 |= 0x04;   // FD_EN
    else
        cfg9 &= ~0x04;
    writeReg(REG_CFG9, cfg9);
}

void AS7341::setLEDCurrent(uint8_t mA) {
    // LED register: bits [6:0] = current (4mA steps), bit 7 = enable
    uint8_t code = mA / 4;
    if (code > 63) code = 63;
    uint8_t led = readReg(REG_LED);
    writeReg(REG_LED, (led & 0x80) | code);
}

void AS7341::enableLED(bool enable) {
    uint8_t led = readReg(REG_LED);
    if (enable)
        led |= 0x80;
    else
        led &= ~0x80;
    writeReg(REG_LED, led);
}

// ─── SMUX Configuration ────────────────────────────────

void AS7341::setSMUXLowChannels() {
    // Switch SMUX to map F1-F4 + Clear + NIR to ADC channels
    writeReg(REG_CFG6, 0x00);  // SMUX_CMD: low channels
}

void AS7341::setSMUXHighChannels() {
    // Switch SMUX to map F5-F8 + Clear to ADC channels
    writeReg(REG_CFG6, 0x10);  // SMUX_CMD: high channels
}

// ─── Wait for Data Ready ────────────────────────────────

bool AS7341::waitForData(uint16_t timeoutMs) {
    unsigned long start = millis();
    while (millis() - start < timeoutMs) {
        uint8_t status = readReg(REG_STATUS2);
        if (status & 0x40) {  // AVALID bit
            // Clear status
            writeReg(REG_STATUS, 0xFF);
            return true;
        }
        delay(5);
    }
    return false;
}

// ─── Channel Reading ────────────────────────────────────

bool AS7341::readLowChannels(float channels[6]) {
    setSMUXLowChannels();

    // Enable spectral measurement: PON + SP_EN
    writeReg(REG_ENABLE, 0x03);

    if (!waitForData()) {
        writeReg(REG_ENABLE, 0x01);  // Disable SP_EN
        return false;
    }

    // Read 6 channels × 2 bytes each from 0x95
    for (int i = 0; i < 6; i++) {
        channels[i] = (float)readReg16(REG_CH0_L + (i * 2));
    }

    writeReg(REG_ENABLE, 0x01);  // Disable SP_EN
    return true;
}

bool AS7341::readHighChannels(float channels[5]) {
    setSMUXHighChannels();

    writeReg(REG_ENABLE, 0x03);

    if (!waitForData()) {
        writeReg(REG_ENABLE, 0x01);
        return false;
    }

    for (int i = 0; i < 5; i++) {
        channels[i] = (float)readReg16(REG_CH0_L + (i * 2));
    }

    writeReg(REG_ENABLE, 0x01);
    return true;
}

// ─── Read All 11 Channels ───────────────────────────────

bool AS7341::readAllChannels(float channels[11]) {
    // Low bank: F1, F2, F3, F4, Clear1, NIR
    float low[6];
    if (!readLowChannels(low)) return false;

    channels[0] = low[0];  // F1 (415nm)
    channels[1] = low[1];  // F2 (445nm)
    channels[2] = low[2];  // F3 (480nm)
    channels[3] = low[3];  // F4 (515nm)
    channels[8] = low[4];  // Clear
    channels[9] = low[5];  // NIR

    delay(10);

    // High bank: F5, F6, F7, F8, Clear2
    float high[5];
    if (!readHighChannels(high)) return false;

    channels[4]  = high[0];  // F5 (555nm)
    channels[5]  = high[1];  // F6 (590nm)
    channels[6]  = high[2];  // F7 (630nm)
    channels[7]  = high[3];  // F8 (680nm)
    channels[10] = high[4];  // Clear2 (or Flicker)

    return true;
}
