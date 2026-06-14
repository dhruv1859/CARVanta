/*
 * WS2812B Status LED Controller — Implementation
 */

#include "leds.h"
#include <math.h>

void StatusLEDs::begin() {
    _leds.begin();
    _leds.setBrightness(_brightness);
    setMode(LEDMode::OFF);
}

void StatusLEDs::setBrightness(uint8_t brightness) {
    _brightness = brightness;
    _leds.setBrightness(brightness);
}

void StatusLEDs::setAll(uint8_t r, uint8_t g, uint8_t b) {
    for (int i = 0; i < NUM_WS2812B_LEDS; i++) {
        _leds.setPixelColor(i, r, g, b);
    }
    _leds.show();
}

void StatusLEDs::breathe(uint8_t r, uint8_t g, uint8_t b) {
    // Sine-wave breathing: 2 second cycle
    float phase = (float)(millis() % 2000) / 2000.0f * 2.0f * PI;
    float intensity = (sinf(phase) + 1.0f) / 2.0f;  // 0.0–1.0

    uint8_t rr = (uint8_t)(r * intensity);
    uint8_t gg = (uint8_t)(g * intensity);
    uint8_t bb = (uint8_t)(b * intensity);

    setAll(rr, gg, bb);
}

void StatusLEDs::setMode(LEDMode mode) {
    _mode = mode;
    _animFrame = 0;

    // Immediate static color for non-animated modes
    switch (mode) {
        case LEDMode::OFF:         setAll(0, 0, 0);       break;
        case LEDMode::SUCCESS:     setAll(0, 80, 80);     break;
        case LEDMode::ERROR:       setAll(100, 0, 0);     break;
        default: break;
    }
}

void StatusLEDs::update() {
    // Only update animated modes at ~30fps
    if (millis() - _lastUpdate < 33) return;
    _lastUpdate = millis();

    switch (_mode) {
        case LEDMode::IDLE:
            breathe(0, 0, 80);    // Blue breathing
            break;
        case LEDMode::MEASURING:
            breathe(0, 100, 0);   // Green breathing
            break;
        case LEDMode::CHARGING:
            breathe(80, 50, 0);   // Amber breathing
            break;
        case LEDMode::LOW_BATTERY:
            breathe(100, 0, 0);   // Red breathing
            break;
        default:
            break;  // Static modes handled in setMode
    }
}
