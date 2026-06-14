/*
 * TCA9548A I2C Multiplexer Driver
 */

#pragma once

#include <Wire.h>
#include <cstdint>

class TCA9548A {
public:
    TCA9548A(uint8_t addr = 0x70) : _addr(addr), _currentChannel(0xFF) {}

    bool begin(TwoWire& wire = Wire);
    bool selectChannel(uint8_t channel);
    void disableAll();
    uint8_t scanBus();  // returns bitmask of responding channels

private:
    uint8_t   _addr;
    uint8_t   _currentChannel;
    TwoWire*  _wire;
};
