/*
 * LSM6DSO 6-Axis IMU — Implementation
 */

#include "lsm6dso.h"

void LSM6DSO::writeReg(uint8_t reg, uint8_t val) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->write(val);
    _wire->endTransmission();
}

uint8_t LSM6DSO::readReg(uint8_t reg) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, (uint8_t)1);
    return _wire->available() ? _wire->read() : 0;
}

void LSM6DSO::readMulti(uint8_t reg, uint8_t* buf, uint8_t len) {
    _wire->beginTransmission(_addr);
    _wire->write(reg);
    _wire->endTransmission(false);
    _wire->requestFrom(_addr, len);
    for (uint8_t i = 0; i < len && _wire->available(); i++) {
        buf[i] = _wire->read();
    }
}

bool LSM6DSO::begin(TwoWire& wire) {
    _wire = &wire;

    // Check WHO_AM_I (should be 0x6C)
    if (readReg(REG_WHO_AM_I) != 0x6C) return false;

    // Software reset
    writeReg(REG_CTRL3_C, 0x01);
    delay(50);

    // Wait for reset complete
    while (readReg(REG_CTRL3_C) & 0x01) delay(1);

    // Enable block data update
    writeReg(REG_CTRL3_C, 0x44);  // BDU + IF_INC

    // Accel: 104Hz ODR, ±4g range
    writeReg(REG_CTRL1_XL, 0x48);
    _accelScale = 0.122f;  // mg/LSB for ±4g

    // Gyro: 104Hz ODR, ±250 dps
    writeReg(REG_CTRL2_G, 0x40);
    _gyroScale = 8.75f;  // mdps/LSB for ±250 dps

    return true;
}

void LSM6DSO::readAccel(float& x, float& y, float& z) {
    uint8_t buf[6];
    readMulti(REG_OUTX_L_A, buf, 6);

    int16_t rawX = (int16_t)(buf[1] << 8 | buf[0]);
    int16_t rawY = (int16_t)(buf[3] << 8 | buf[2]);
    int16_t rawZ = (int16_t)(buf[5] << 8 | buf[4]);

    x = rawX * _accelScale / 1000.0f;  // mg → g
    y = rawY * _accelScale / 1000.0f;
    z = rawZ * _accelScale / 1000.0f;
}

void LSM6DSO::readGyro(float& x, float& y, float& z) {
    uint8_t buf[6];
    readMulti(REG_OUTX_L_G, buf, 6);

    int16_t rawX = (int16_t)(buf[1] << 8 | buf[0]);
    int16_t rawY = (int16_t)(buf[3] << 8 | buf[2]);
    int16_t rawZ = (int16_t)(buf[5] << 8 | buf[4]);

    x = rawX * _gyroScale / 1000.0f;  // mdps → dps
    y = rawY * _gyroScale / 1000.0f;
    z = rawZ * _gyroScale / 1000.0f;
}

float LSM6DSO::readTemperature() {
    uint8_t buf[2];
    readMulti(REG_TEMP_L, buf, 2);
    int16_t raw = (int16_t)(buf[1] << 8 | buf[0]);
    return 25.0f + raw / 256.0f;
}

void LSM6DSO::setAccelRange(uint8_t g) {
    uint8_t val = readReg(REG_CTRL1_XL) & 0xF3;
    switch (g) {
        case 2:  val |= 0x00; _accelScale = 0.061f; break;
        case 4:  val |= 0x08; _accelScale = 0.122f; break;
        case 8:  val |= 0x0C; _accelScale = 0.244f; break;
        case 16: val |= 0x04; _accelScale = 0.488f; break;
        default: return;
    }
    writeReg(REG_CTRL1_XL, val);
}

void LSM6DSO::setGyroRange(uint16_t dps) {
    uint8_t val = readReg(REG_CTRL2_G) & 0xF1;
    switch (dps) {
        case 125:  val |= 0x02; _gyroScale = 4.375f;  break;
        case 250:  val |= 0x00; _gyroScale = 8.75f;   break;
        case 500:  val |= 0x04; _gyroScale = 17.50f;  break;
        case 1000: val |= 0x08; _gyroScale = 35.0f;   break;
        case 2000: val |= 0x0C; _gyroScale = 70.0f;   break;
        default: return;
    }
    writeReg(REG_CTRL2_G, val);
}

void LSM6DSO::setAccelODR(uint16_t hz) {
    uint8_t val = readReg(REG_CTRL1_XL) & 0x0F;
    switch (hz) {
        case 12:  val |= 0x10; break;
        case 26:  val |= 0x20; break;
        case 52:  val |= 0x30; break;
        case 104: val |= 0x40; break;
        case 208: val |= 0x50; break;
        case 416: val |= 0x60; break;
        case 833: val |= 0x70; break;
        default:  val |= 0x40; break;
    }
    writeReg(REG_CTRL1_XL, val);
}

void LSM6DSO::setGyroODR(uint16_t hz) {
    uint8_t val = readReg(REG_CTRL2_G) & 0x0F;
    switch (hz) {
        case 12:  val |= 0x10; break;
        case 26:  val |= 0x20; break;
        case 52:  val |= 0x30; break;
        case 104: val |= 0x40; break;
        case 208: val |= 0x50; break;
        case 416: val |= 0x60; break;
        case 833: val |= 0x70; break;
        default:  val |= 0x40; break;
    }
    writeReg(REG_CTRL2_G, val);
}
