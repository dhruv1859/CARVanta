/*
 * TCA9548A I2C Multiplexer Driver — Implementation
 */

#include "i2c_mux.h"

bool TCA9548A::begin(TwoWire& wire) {
    _wire = &wire;
    _wire->beginTransmission(_addr);
    return (_wire->endTransmission() == 0);
}

bool TCA9548A::selectChannel(uint8_t channel) {
    if (channel > 7) return false;
    if (channel == _currentChannel) return true;  // already selected

    _wire->beginTransmission(_addr);
    _wire->write(1 << channel);
    bool ok = (_wire->endTransmission() == 0);
    if (ok) _currentChannel = channel;
    return ok;
}

void TCA9548A::disableAll() {
    _wire->beginTransmission(_addr);
    _wire->write(0x00);
    _wire->endTransmission();
    _currentChannel = 0xFF;
}

uint8_t TCA9548A::scanBus() {
    uint8_t found = 0;
    for (uint8_t ch = 0; ch < 8; ch++) {
        selectChannel(ch);
        // Scan for any device on this channel
        for (uint8_t addr = 0x08; addr < 0x78; addr++) {
            _wire->beginTransmission(addr);
            if (_wire->endTransmission() == 0) {
                found |= (1 << ch);
                break;  // at least one device on this channel
            }
        }
    }
    disableAll();
    return found;
}
