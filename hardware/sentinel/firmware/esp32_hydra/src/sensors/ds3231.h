/*
 * DS3231 Real-Time Clock Driver
 */

#pragma once

#include <Wire.h>
#include <cstdint>

struct DateTime {
    uint8_t  second, minute, hour;
    uint8_t  dayOfWeek;
    uint8_t  day, month;
    uint16_t year;
};

class DS3231 {
public:
    DS3231(uint8_t addr = 0x68) : _addr(addr) {}

    bool     begin(TwoWire& wire = Wire);
    DateTime getDateTime();
    void     setDateTime(const DateTime& dt);
    float    getTemperature();   // Built-in temp sensor (±3°C)
    uint32_t getEpoch();         // Simplified epoch (seconds since 2000-01-01)

private:
    uint8_t  _addr;
    TwoWire* _wire;

    uint8_t  bcdToDec(uint8_t bcd);
    uint8_t  decToBcd(uint8_t dec);
    void     writeReg(uint8_t reg, uint8_t val);
    uint8_t  readReg(uint8_t reg);
};
