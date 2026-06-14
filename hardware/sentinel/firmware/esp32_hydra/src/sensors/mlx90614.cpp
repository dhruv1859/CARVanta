/*
 * MLX90614 Infrared Temperature Sensor — Implementation
 */

#include "mlx90614.h"

bool MLX90614::begin(TwoWire& wire) {
    _wire = &wire;
    // Test communication by reading ambient temp
    uint16_t raw = readReg16(REG_AMBIENT);
    return (raw != 0 && raw != 0xFFFF);
}

uint16_t MLX90614::readReg16(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)3);  // 2 data + 1 PEC (CRC)

    if (_wire->available() < 3) return 0;

    uint8_t lsb = _wire->read();
    uint8_t msb = _wire->read();
    uint8_t pec = _wire->read();  // CRC-8

    // Verify CRC
    uint8_t crcBuf[] = {(uint8_t)(_addr << 1), reg,
                        (uint8_t)((_addr << 1) | 1), lsb, msb};
    if (crc8(crcBuf, 5) != pec) return 0;  // CRC mismatch

    return (uint16_t)(msb << 8) | lsb;
}

float MLX90614::rawToTemp(uint16_t raw) {
    return raw * 0.02f - 273.15f;  // Kelvin to Celsius
}

float MLX90614::readObjectTemp() {
    uint16_t raw = readReg16(REG_OBJECT1);
    if (raw == 0) return -999.0f;
    return rawToTemp(raw);
}

float MLX90614::readAmbientTemp() {
    uint16_t raw = readReg16(REG_AMBIENT);
    if (raw == 0) return -999.0f;
    return rawToTemp(raw);
}

float MLX90614::readEmissivity() {
    uint16_t raw = readReg16(REG_EMISSIVITY);
    return raw / 65535.0f;
}

bool MLX90614::setEmissivity(float emissivity) {
    if (emissivity < 0.1f || emissivity > 1.0f) return false;
    // Writing EEPROM requires special sequence — not implemented for safety
    return false;
}

uint8_t MLX90614::crc8(uint8_t* data, uint8_t len) {
    uint8_t crc = 0;
    for (uint8_t i = 0; i < len; i++) {
        crc ^= data[i];
        for (uint8_t j = 0; j < 8; j++) {
            if (crc & 0x80)
                crc = (crc << 1) ^ 0x07;
            else
                crc <<= 1;
        }
    }
    return crc;
}
