/*
 * Heater PID Controller — Implementation
 */

#include "heater_pid.h"

void HeaterPID::begin() {
    pinMode(PIN_HEATER_PWM, OUTPUT);
    analogWrite(PIN_HEATER_PWM, 0);
    _enabled = false;
}

void HeaterPID::enable(float targetTemp) {
    _targetTemp = targetTemp;
    _integral = 0;
    _prevError = 0;
    _enabled = true;
    Serial.printf("[PID] Heater ON, target=%.1f°C\n", targetTemp);
}

void HeaterPID::disable() {
    _enabled = false;
    _integral = 0;
    _prevError = 0;
    _output = 0;
    analogWrite(PIN_HEATER_PWM, 0);
    Serial.println("[PID] Heater OFF");
}

void HeaterPID::setTuning(float kp, float ki, float kd) {
    _kp = kp;
    _ki = ki;
    _kd = kd;
}

void HeaterPID::setMaxDuty(uint8_t maxDuty) {
    _maxDuty = maxDuty;
}

void HeaterPID::update(float currentTemp) {
    if (!_enabled) {
        analogWrite(PIN_HEATER_PWM, 0);
        return;
    }

    // ─── Safety Check: Over-temperature shutdown ────────
    if (currentTemp > HEATER_MAX_TEMP) {
        Serial.printf("[PID] OVER-TEMP SHUTDOWN! %.1f°C > %.1f°C limit\n",
                      currentTemp, HEATER_MAX_TEMP);
        disable();
        return;
    }

    // ─── PID Calculation ────────────────────────────────
    float dt = HEATER_PID_INTERVAL_MS / 1000.0f;  // seconds

    float error = _targetTemp - currentTemp;

    // Proportional
    float pTerm = _kp * error;

    // Integral with anti-windup clamping
    _integral += error * dt;
    if (_integral > 100.0f)  _integral = 100.0f;
    if (_integral < -100.0f) _integral = -100.0f;
    float iTerm = _ki * _integral;

    // Derivative
    float derivative = (error - _prevError) / dt;
    float dTerm = _kd * derivative;
    _prevError = error;

    // Output
    _output = pTerm + iTerm + dTerm;

    // Clamp output to valid PWM range
    if (_output < 0.0f) _output = 0.0f;
    if (_output > (float)_maxDuty) _output = (float)_maxDuty;

    analogWrite(PIN_HEATER_PWM, (int)_output);
}
