/*
 * WS2812B Status LED Controller
 */

#pragma once

#include <Adafruit_NeoPixel.h>
#include "pins.h"

enum class LEDMode : uint8_t {
    OFF, IDLE, MEASURING, ERROR, SUCCESS, CHARGING, LOW_BATTERY
};

class StatusLEDs {
public:
    void begin();
    void setMode(LEDMode mode);
    void update();  // call in loop for animations
    void setBrightness(uint8_t brightness);

private:
    Adafruit_NeoPixel _leds{NUM_WS2812B_LEDS, PIN_LED_DATA, NEO_GRB + NEO_KHZ800};
    LEDMode           _mode = LEDMode::OFF;
    unsigned long     _lastUpdate = 0;
    uint8_t           _animFrame = 0;
    uint8_t           _brightness = 80;

    void setAll(uint8_t r, uint8_t g, uint8_t b);
    void breathe(uint8_t r, uint8_t g, uint8_t b);
};
