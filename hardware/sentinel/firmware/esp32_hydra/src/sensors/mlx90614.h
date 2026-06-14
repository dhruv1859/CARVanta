/*
 * MLX90614 Infrared Temperature Sensor Driver
 * Uses SMBus protocol (not standard I2C)
 */

#pragma once

#include <Wire.h>
#include <cstdint>

class MLX90614 {
public:
    MLX90614(uint8_t addr = 0x5A) : _addr(addr) {}

    bool  begin(TwoWire& wire = Wire);
    float readObjectTemp();    // °C
    float readAmbientTemp();   // °C
    float readEmissivity();
    bool  setEmissivity(float emissivity);  // 0.1–1.0

private:
    uint8_t   _addr;
    TwoWire*  _wire;

    uint16_t readReg16(uint8_t reg);
    float    rawToTemp(uint16_t raw);
    uint8_t  crc8(uint8_t* data, uint8_t len);

    static constexpr uint8_t REG_AMBIENT  = 0x06;
    static constexpr uint8_t REG_OBJECT1  = 0x07;
    static constexpr uint8_t REG_EMISSIVITY = 0x24;
};
