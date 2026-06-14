/*
 * Hardware Watchdog Timer
 */

#pragma once

#include <Arduino.h>
#include "config.h"

class Watchdog {
public:
    void begin(uint32_t timeoutSeconds = WATCHDOG_TIMEOUT_S);
    void feed();  // Reset watchdog timer
    void disable();
};
