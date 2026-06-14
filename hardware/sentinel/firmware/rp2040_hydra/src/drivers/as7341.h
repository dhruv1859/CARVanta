/*
 * AS7341 11-Channel Spectral Sensor Driver
 */

#pragma once

#include <Wire.h>
#include <cstdint>
#include "config.h"

class AS7341 {
public:
    AS7341(uint8_t addr = I2C_ADDR_AS7341) : _addr(addr) {}

    bool begin(TwoWire& wire);
    bool readAllChannels(float channels[11]);

    // Configuration
    void setIntegrationTime(uint8_t atime);    // 0–255 (2.78ms steps)
    void setGain(uint8_t gain);                // 0=0.5x, 1=1x, ... 10=512x
    void enableFlickerDetection(bool enable);

    // LED control (built-in LED driver)
    void setLEDCurrent(uint8_t mA);            // 0–258mA
    void enableLED(bool enable);

private:
    uint8_t   _addr;
    TwoWire*  _wire;

    bool readLowChannels(float channels[6]);   // F1-F4, Clear, NIR
    bool readHighChannels(float channels[5]);  // F5-F8, Clear
    void setSMUXLowChannels();
    void setSMUXHighChannels();
    bool waitForData(uint16_t timeoutMs = 1000);

    void writeReg(uint8_t reg, uint8_t val);
    uint8_t readReg(uint8_t reg);
    uint16_t readReg16(uint8_t reg);

    static constexpr uint8_t REG_ENABLE   = 0x80;
    static constexpr uint8_t REG_ATIME    = 0x81;
    static constexpr uint8_t REG_WTIME    = 0x83;
    static constexpr uint8_t REG_CONFIG   = 0x70;
    static constexpr uint8_t REG_CFG0     = 0xA9;
    static constexpr uint8_t REG_CFG1     = 0xAA;
    static constexpr uint8_t REG_CFG6     = 0xAF;
    static constexpr uint8_t REG_CFG9     = 0xB2;
    static constexpr uint8_t REG_STATUS   = 0x93;
    static constexpr uint8_t REG_STATUS2  = 0xA3;
    static constexpr uint8_t REG_CH0_L    = 0x95;
    static constexpr uint8_t REG_LED      = 0x74;
    static constexpr uint8_t REG_ID       = 0x92;
};
