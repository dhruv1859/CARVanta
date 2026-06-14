/*
 * Power Manager — Deep sleep, battery monitoring, charge status
 */

#pragma once

#include <Arduino.h>
#include "config.h"
#include "pins.h"

class PowerManager {
public:
    void begin();
    bool isCharging();
    bool isPowerGood();
    bool isBatteryAlert();
    void enterDeepSleep(uint32_t sleepSeconds);
    void checkCriticalBattery(float soc);  // auto-sleep if critical

private:
    void configureWakeSource();
};
