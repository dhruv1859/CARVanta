/*
 * MAX17048 Fuel Gauge Driver
 */

#pragma once

#include <Wire.h>
#include <cstdint>

class MAX17048 {
public:
    MAX17048(uint8_t addr = 0x36) : _addr(addr) {}

    bool  begin(TwoWire& wire = Wire);
    float getSOC();        // State of charge (%)
    float getVoltage();    // Cell voltage (V)
    float getRate();       // Charge/discharge rate (%/hr)
    void  setAlertThreshold(uint8_t percent);  // Low-SOC alert
    bool  isAlertActive();
    void  clearAlert();
    void  quickStart();    // Force re-estimation
    void  sleep();
    void  wake();

private:
    uint8_t   _addr;
    TwoWire*  _wire;

    uint16_t readReg16(uint8_t reg);
    void     writeReg16(uint8_t reg, uint16_t val);

    static constexpr uint8_t REG_VCELL   = 0x02;
    static constexpr uint8_t REG_SOC     = 0x04;
    static constexpr uint8_t REG_MODE    = 0x06;
    static constexpr uint8_t REG_VERSION = 0x08;
    static constexpr uint8_t REG_CONFIG  = 0x0C;
    static constexpr uint8_t REG_CRATE   = 0x16;
    static constexpr uint8_t REG_CMD     = 0xFE;
};
