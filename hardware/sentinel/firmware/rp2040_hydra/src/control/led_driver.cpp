/*
 * Excitation LED Driver — Implementation
 */

#include "led_driver.h"

void LEDDriver::begin() {
    for (int i = 0; i < 3; i++) {
        pinMode(_pins[i], OUTPUT);
        digitalWrite(_pins[i], LOW);
        _state[i] = false;
    }
}

void LEDDriver::enable(ExcitationLED led) {
    uint8_t idx = (uint8_t)led;
    if (idx > 2) return;

    digitalWrite(_pins[idx], HIGH);
    _state[idx] = true;
    _onTime[idx] = millis();
    Serial.printf("[LED] Excitation LED %d ON\n", idx);
}

void LEDDriver::disable(ExcitationLED led) {
    uint8_t idx = (uint8_t)led;
    if (idx > 2) return;

    digitalWrite(_pins[idx], LOW);
    _state[idx] = false;
    Serial.printf("[LED] Excitation LED %d OFF\n", idx);
}

void LEDDriver::disableAll() {
    for (int i = 0; i < 3; i++) {
        digitalWrite(_pins[i], LOW);
        _state[i] = false;
    }
}

bool LEDDriver::isOn(ExcitationLED led) const {
    uint8_t idx = (uint8_t)led;
    return (idx <= 2) ? _state[idx] : false;
}

void LEDDriver::update() {
    // Auto-off safety: disable any LED on longer than timeout
    for (int i = 0; i < 3; i++) {
        if (_state[i] && (millis() - _onTime[i] > LED_AUTO_OFF_MS)) {
            Serial.printf("[LED] Safety timeout: LED %d auto-OFF after %lums\n",
                          i, LED_AUTO_OFF_MS);
            digitalWrite(_pins[i], LOW);
            _state[i] = false;
        }
    }
}
