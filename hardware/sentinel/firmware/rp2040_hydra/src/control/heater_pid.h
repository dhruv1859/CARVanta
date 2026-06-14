/*
 * Heater PID Controller with Safety Limits
 */

#pragma once

#include <Arduino.h>
#include "config.h"
#include "pins.h"

class HeaterPID {
public:
    void begin();
    void update(float currentTemp);  // call at HEATER_PID_INTERVAL_MS rate
    void enable(float targetTemp);
    void disable();
    void setTuning(float kp, float ki, float kd);
    void setMaxDuty(uint8_t maxDuty);

    bool  isEnabled() const { return _enabled; }
    float getTarget() const { return _targetTemp; }
    float getOutput() const { return _output; }

private:
    bool  _enabled = false;
    float _targetTemp = HEATER_TARGET_TEMP;
    float _kp = PID_KP_DEFAULT;
    float _ki = PID_KI_DEFAULT;
    float _kd = PID_KD_DEFAULT;
    float _integral = 0;
    float _prevError = 0;
    float _output = 0;
    uint8_t _maxDuty = HEATER_MAX_DUTY;
};
