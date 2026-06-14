/*
 * Excitation LED Driver (UV, Blue, White)
 * Safety timeout to prevent overheating
 */

#pragma once

#include <Arduino.h>
#include "config.h"
#include "pins.h"

enum class ExcitationLED : uint8_t {
    UV    = 0,  // 365nm
    BLUE  = 1,  // 470nm
    WHITE = 2
};

class LEDDriver {
public:
    void begin();
    void enable(ExcitationLED led);
    void disable(ExcitationLED led);
    void disableAll();
    void update();  // call in loop — handles auto-off timeout

    bool isOn(ExcitationLED led) const;

private:
    uint8_t       _pins[3] = {PIN_UV_LED_EN, PIN_BLUE_LED_EN, PIN_WHITE_LED_EN};
    bool          _state[3] = {false, false, false};
    unsigned long _onTime[3] = {0, 0, 0};
};
