/*
 * TMP117 High-Precision Temperature Sensor Driver
 * Accuracy: ±0.1°C from –20°C to +50°C
 */

#pragma once

#include <Wire.h>
#include <cstdint>
#include "config.h"

class TMP117 {
public:
    TMP117(uint8_t addr = I2C_ADDR_TMP117) : _addr(addr) {}

    bool  begin(TwoWire& wire);
    float readTemperature();               // °C, ±0.1°C accuracy
    void  setAlertLimits(float low, float high);
    bool  isAlertActive();
    void  setOneShotMode();
    void  setContinuousMode();

private:
    uint8_t   _addr;
    TwoWire*  _wire;

    void     writeReg16(uint8_t reg, uint16_t val);
    uint16_t readReg16(uint8_t reg);

    static constexpr uint8_t REG_TEMP_RESULT = 0x00;
    static constexpr uint8_t REG_CONFIG      = 0x01;
    static constexpr uint8_t REG_HIGH_LIMIT  = 0x02;
    static constexpr uint8_t REG_LOW_LIMIT   = 0x03;
    static constexpr uint8_t REG_DEVICE_ID   = 0x0F;
};
